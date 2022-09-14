"""
Insert elements extracted from the Slurm reports into the database.
"""

import os, time
from pymongo import UpdateOne
import json
from slurm_state.extra_filters import (
    is_allocation_related_to_mila,
    clusters_valid,
)

from slurm_state.helpers.gpu_helper import get_cw_gres_description
from slurm_state.config import get_config, timezone, string, optional_string

from .scontrol_parser import job_parser, node_parser


clusters_valid.add_field("timezone", timezone)
clusters_valid.add_field("account_field", string)
clusters_valid.add_field("update_field", optional_string)


def pprint_bulk_result(result):
    if "upserted" in result.bulk_api_result:
        # too long and not necessary
        del result.bulk_api_result["upserted"]
    print(result.bulk_api_result)


def fetch_slurm_report_jobs(cluster_name, scontrol_report_path):
    return _fetch_slurm_report_helper(job_parser, cluster_name, scontrol_report_path)


def fetch_slurm_report_nodes(cluster_name, scontrol_report_path):
    return _fetch_slurm_report_helper(node_parser, cluster_name, scontrol_report_path)


def _fetch_slurm_report_helper(parser, cluster_name, scontrol_report_path):
    """

    Yields elements ready to be slotted into the "slurm" field,
    but they have to be processed further before committing to mongodb.
    """

    assert os.path.exists(
        scontrol_report_path
    ), f"scontrol_report_path {scontrol_report_path} is missing."

    ctx = get_config("clusters").get(cluster_name, None)
    assert ctx is not None, f"{cluster_name} not configured"

    with open(scontrol_report_path, "r") as f:
        for e in parser(f, ctx):
            e["cluster_name"] = cluster_name
            yield e


def slurm_job_to_clockwork_job(slurm_job: dict):
    """
    Takes the components returned from the slurm reports,
    and turns it into a dict with 3 subcomponents.
    That can later be committed to mongodb in the format
    that clockwork expects.
    """
    clockwork_job = {
        "slurm": slurm_job,
        "cw": {
            "mila_email_username": None,
        },
        "user": {},
    }
    return clockwork_job


def lookup_user_account(users_collection):
    """
    Mutates the argument in order to fill in the
    field for "cw" pertaining to the user account.
    Returns the mutated value to facilitate a `map` call.
    """

    def _lookup_user_account(clockwork_job: dict[dict]):
        cluster_name = clockwork_job["slurm"]["cluster_name"]
        cluster_username = clockwork_job["slurm"]["username"]

        account_field = get_config("clusters")[cluster_name]["account_field"]
        result = users_collection.find_one({account_field: cluster_username})
        if result is not None:
            clockwork_job["cw"]["mila_email_username"] = result["mila_email_username"]

        return clockwork_job

    return _lookup_user_account


def slurm_node_to_clockwork_node(slurm_node: dict):
    """
    Similar to slurm_job_to_clockwork_job,
    but without the "user" field and without a need
    to infer user accounts (because nodes don't belong
    to specific users).
    We still add the "cw" field for our own uses.
    """

    # If GPU information are available on the node
    if (
        all(key in slurm_node for key in ["gres", "features"])
        and slurm_node["gres"] is not None
    ):
        # Parse the GPU data and add it to the "cw" field
        gpu_data = get_cw_gres_description(slurm_node["gres"], slurm_node["features"])

        # Set up the node dictionary as used in Clockwork
        clockwork_node = {
            "slurm": slurm_node,
            "cw": {"gpu": gpu_data},
        }
    # Otherwise
    else:
        clockwork_node = {
            "slurm": slurm_node,
            "cw": {"gpu": {}},
        }

    return clockwork_node


def main_read_jobs_and_update_collection(
    jobs_collection,
    users_collection,
    cluster_name,
    scontrol_show_job_path,
    want_commit_to_db=True,
    dump_file="",
):

    # What we want is to create the entry as
    #    {"slurm": slurm_dict, "cw": cw_dict, "user": user_dict}
    # if it's not present in the database,
    # but if it actually is already there then we only want
    # to update the "slurm" part of it.

    # Note that adding an extra {"$set": {"cw.last_slurm_update": time.time()}}
    # after the $setOnInsert operator does not work with mongodb.

    timestamp_start = time.time()
    L_updates_to_do = []
    L_user_updates = []
    L_data_for_dump_file = []

    clusters = get_config("clusters")

    for D_job in map(
        lookup_user_account(users_collection),
        filter(
            is_allocation_related_to_mila,
            map(
                slurm_job_to_clockwork_job,
                fetch_slurm_report_jobs(cluster_name, scontrol_show_job_path),
            ),
        ),
    ):

        L_data_for_dump_file.append(D_job)

        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {
                    "slurm.job_id": D_job["slurm"]["job_id"],
                    "slurm.cluster_name": D_job["slurm"]["cluster_name"],
                },
                # the data that we write in the collection
                {
                    "$set": {"slurm": D_job["slurm"]},
                    "$setOnInsert": {"cw": D_job["cw"], "user": D_job["user"]},
                },
                # create if missing, update if present
                upsert=True,
            )
        )

        # Here we can add set extra values to "cw".
        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {
                    "slurm.job_id": D_job["slurm"]["job_id"],
                    "slurm.cluster_name": D_job["slurm"]["cluster_name"],
                },
                # the data that we write in the collection
                {
                    "$set": {
                        "cw.last_slurm_update": time.time(),
                        "cw.mila_email_username": D_job["cw"]["mila_email_username"],
                    }
                },
                # create if missing, update if present
                upsert=False,
            )
        )

        # Register accounts from job keys
        comment = D_job["slurm"].get("comment", None)
        marker = "clockwork_register_account:"
        if comment is not None and comment.startswith(marker):
            key = comment[len(marker) :]
            cluster_info = clusters[D_job["slurm"]["cluster_name"]]
            account_field = cluster_info["account_field"]
            update_field = cluster_info["update_field"]

            if update_field:
                username = D_job["slurm"][account_field]
                L_user_updates.append(
                    UpdateOne(
                        {update_field: key},
                        {
                            "$set": {
                                account_field: username,
                                update_field: None,
                            }
                        },
                    )
                )

    if want_commit_to_db:
        if L_updates_to_do:
            assert jobs_collection is not None
            print("jobs_collection.bulk_write(L_updates_to_do)")
            result = jobs_collection.bulk_write(L_updates_to_do)  #  <- the actual work
            pprint_bulk_result(result)
        else:
            print(
                "Empty list found for update to jobs_collection."
                "This is unexpected and might be the sign of a problem."
            )

        if L_user_updates:
            print("results = users_collection.bulk_write(L_user_updates, upsert=False)")
            result = users_collection.bulk_write(
                L_user_updates,
                upsert=False,  # this should never create new users.
            )
            pprint_bulk_result(result)

        mongo_update_duration = time.time() - timestamp_start
        print(
            f"Bulk write for {len(L_updates_to_do)} job entries in mongodb took {mongo_update_duration} seconds."
        )

    if dump_file:
        with open(dump_file, "w") as f:
            json.dump(L_data_for_dump_file, f, indent=4)
        print(f"Wrote to dump_file {dump_file}.")


def main_read_nodes_and_update_collection(
    nodes_collection,
    cluster_desc_path,
    scontrol_show_node_path,
    want_commit_to_db=True,
    dump_file="",
):

    # What we want is to create the entry as
    #    {"slurm": slurm_dict, "cw": cw_dict}
    # if it's not present in the database,
    # but if it actually is already there then we only want
    # to update the "slurm" part of it.

    timestamp_start = time.time()
    L_updates_to_do = []
    L_data_for_dump_file = []

    for D_node in map(
        slurm_node_to_clockwork_node,
        fetch_slurm_report_nodes(cluster_desc_path, scontrol_show_node_path),
    ):

        L_data_for_dump_file.append(D_node)

        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {
                    "slurm.name": D_node["slurm"]["name"],
                    "slurm.cluster_name": D_node["slurm"]["cluster_name"],
                },
                # the data that we write in the collection
                {
                    "$set": {"slurm": D_node["slurm"]},
                    "$setOnInsert": {"cw": D_node["cw"]},
                },
                # create if missing, update if present
                upsert=True,
            )
        )

        # Here we can add set extra values to "cw".
        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {
                    "slurm.name": D_node["slurm"]["name"],
                    "slurm.cluster_name": D_node["slurm"]["cluster_name"],
                },
                # the data that we write in the collection
                {"$set": {"cw.last_slurm_update": time.time()}},
                # create if missing, update if present
                upsert=False,
            )
        )

    if want_commit_to_db:
        if L_updates_to_do:
            assert nodes_collection is not None
            print("nodes_collection.bulk_write(L_updates_to_do)")
            result = nodes_collection.bulk_write(L_updates_to_do)  #  <- the actual work
            pprint_bulk_result(result)
        else:
            print(
                "Empty list found for update to nodes_collection."
                "This is unexpected and might be the sign of a problem."
            )

        mongo_update_duration = time.time() - timestamp_start
        print(
            f"Bulk write for {len(L_updates_to_do)} node entries in mongodb took {mongo_update_duration} seconds."
        )

    if dump_file:
        with open(dump_file, "w") as f:
            json.dump(L_data_for_dump_file, f, indent=4)
        print(f"Wrote to dump_file {dump_file}.")


def main_read_users_and_update_collection(
    users_collection,
    users_json_file,
):

    timestamp_start = time.time()
    L_updates_to_do = []

    with open(users_json_file, "r") as f:
        users_to_store = json.load(f)

    for user_to_store in users_to_store:

        # Add the user to the queue of updates to do
        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {"mila_email_username": user_to_store["mila_email_username"]},
                # the data that we write in the collection
                {"$set": user_to_store},
                # create if missing, update if present
                upsert=True,
            )
        )

    if L_updates_to_do:
        print("result = users_collection.bulk_write(L_updates_to_do)")
        result = users_collection.bulk_write(L_updates_to_do)
        pprint_bulk_result(result)
    mongo_update_duration = time.time() - timestamp_start
    print(
        f"Bulk write for {len(L_updates_to_do)} user entries in mongodb took {mongo_update_duration} seconds."
    )
