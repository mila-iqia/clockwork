import os, time
from .mongo_client import get_mongo_client
from pymongo import UpdateOne
import json
import zoneinfo

from .scontrol_parser import job_parser, node_parser


def fetch_slurm_report_jobs(cluster_desc_path, scontrol_report_path):
    return _fetch_slurm_report_helper(
        job_parser, cluster_desc_path, scontrol_report_path
    )


def fetch_slurm_report_nodes(cluster_desc_path, scontrol_report_path):
    return _fetch_slurm_report_helper(
        node_parser, cluster_desc_path, scontrol_report_path
    )


def _fetch_slurm_report_helper(parser, cluster_desc_path, scontrol_report_path):
    """

    Yields elements ready to be slotted into the "slurm" field,
    but they have to be processed further before committing to mongodb.
    """

    assert os.path.exists(
        cluster_desc_path
    ), f"cluster_desc_path {cluster_desc_path} is missing."
    assert os.path.exists(
        scontrol_report_path
    ), f"scontrol_report_path {scontrol_report_path} is missing."

    with open(cluster_desc_path, "r") as f:
        ctx = json.load(f)
        ctx["timezone"] = zoneinfo.ZoneInfo(ctx["timezone"])

    with open(scontrol_report_path, "r") as f:
        for e in parser(f, ctx):
            e["cluster_name"] = ctx["name"]
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
            "cc_account_username": None,
            "mila_account_username": None,
            "mila_email_username": None,
        },
        "user": {},
    }
    infer_user_accounts(clockwork_job)  # mutates argument
    return clockwork_job


def infer_user_accounts(clockwork_job: dict[dict]):
    """
    Mutates the argument in order to fill in the
    fields for "cw" pertaining to the user accounts.
    Returns the mutated value to facilitate a `map` call.
    """
    # One of the fields is bound to be known. We can add that one,
    # and leave the other ones empty for now.
    for k in ["cc_account_username", "mila_account_username", "mila_email_username"]:
        if clockwork_job["slurm"].get(k, "") not in ["", None]:
            clockwork_job["cw"][k] = clockwork_job["slurm"][k]
    return clockwork_job


def slurm_node_to_clockwork_node(slurm_node: dict):
    """
    Similar to slurm_job_to_clockwork_job,
    but without the "user" field and without a need
    to infer user accounts (because nodes don't belong
    to specific users).
    We still add the "cw" field for our own uses.
    """
    clockwork_node = {
        "slurm": slurm_node,
        "cw": {},
    }
    return clockwork_node


def main_read_jobs_and_update_collection(
    jobs_collection,
    cluster_desc_path,
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
    L_data_for_dump_file = []

    for D_job in map(
        infer_user_accounts,
        map(
            slurm_job_to_clockwork_job,
            fetch_slurm_report_jobs(cluster_desc_path, scontrol_show_job_path),
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
                {"$set": {"cw.last_slurm_update": time.time()}},
                # create if missing, update if present
                upsert=False,
            )
        )

    if want_commit_to_db:
        result = jobs_collection.bulk_write(L_updates_to_do)  #  <- the actual work
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
        result = nodes_collection.bulk_write(L_updates_to_do)  #  <- the actual work
        # print(result.bulk_api_result)
        mongo_update_duration = time.time() - timestamp_start
        print(
            f"Bulk write for {len(L_updates_to_do)} node entries in mongodb took {mongo_update_duration} seconds."
        )

    if dump_file:
        with open(dump_file, "w") as f:
            json.dump(L_data_for_dump_file, f, indent=4)
        print(f"Wrote to dump_file {dump_file}.")
