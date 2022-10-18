"""
Insert elements extracted from the Slurm reports into the database.
"""

import os, time
import copy
from pymongo import UpdateOne, InsertOne, ReplaceOne
import json
from slurm_state.extra_filters import (
    is_allocation_related_to_mila,
    clusters_valid,
)

from slurm_state.helpers.gpu_helper import get_cw_gres_description
from slurm_state.config import get_config, timezone, string, optional_string, boolean

from slurm_state.scontrol_parser import job_parser, node_parser
from slurm_state.sacct_access import fetch_data_with_sacct_on_remote_clusters


clusters_valid.add_field("timezone", timezone)
clusters_valid.add_field("account_field", string)
clusters_valid.add_field("update_field", optional_string)
clusters_valid.add_field("remote_user", optional_string)
clusters_valid.add_field("remote_hostname", optional_string)
clusters_valid.add_field("sacct_enabled", boolean)


# Might as well share this as a global variable if it's useful later.
NOT_TERMINAL_JOB_STATES = ["RUNNING", "PENDING", "COMPLETING"]


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
    want_sacct=True,
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

    def append_data_for_dump_file(D_job):
        # just omit the "_id" part of it
        L_data_for_dump_file.append({k: D_job[k] for k in D_job.keys() if k != "_id"})

    clusters = get_config("clusters")
    assert cluster_name in clusters
    now = time.time()

    # Contrary to the previous approach, we'll fetch everything two
    # operations and then we'll sort out the three cases:
    #    - update to existing job from an scontrol job
    #    - initial insertion from an scontrol job
    #    - update to existing job from an sacct call

    # Note that since we filter for a single "cluster_name",
    # this means that "job_id" can be taken as unique
    # identifiers to match jobs in this context.

    LD_jobs_currently_in_mongodb = list(
        jobs_collection.find({"slurm.cluster_name": cluster_name})
    )
    # index by job_id for O(1) lookup in the next step where we match jobs from db and scontrol
    DD_jobs_currently_in_mongodb = dict(
        (D_job["slurm"]["job_id"], D_job) for D_job in LD_jobs_currently_in_mongodb
    )

    LD_jobs_scontrol = list(
        map(
            lookup_user_account(users_collection),
            filter(
                is_allocation_related_to_mila,
                map(
                    slurm_job_to_clockwork_job,
                    fetch_slurm_report_jobs(cluster_name, scontrol_show_job_path),
                ),
            ),
        )
    )
    DD_jobs_scontrol = dict(
        (D_job["slurm"]["job_id"], D_job) for D_job in LD_jobs_scontrol
    )

    L_job_ids_to_retrieve_with_sacct = set(
        [
            job_id
            for (job_id, D_job) in DD_jobs_currently_in_mongodb.items()
            if (job_id not in DD_jobs_scontrol)
            and (D_job["slurm"]["job_state"] in NOT_TERMINAL_JOB_STATES)
        ]
    )

    L_job_ids_to_insert = set(DD_jobs_scontrol.keys()) - set(
        DD_jobs_currently_in_mongodb.keys()
    )
    L_job_ids_to_update = set(DD_jobs_scontrol.keys()).intersection(
        set(DD_jobs_currently_in_mongodb.keys())
    )

    # The way we partitioned those job_id, they cannot be in two of those sets.
    # Note that many job_id for old jobs are not going to be found in any of those sets
    # because they simply do not require exceptional handling by sacct.
    assert L_job_ids_to_insert.isdisjoint(L_job_ids_to_update)
    assert L_job_ids_to_update.isdisjoint(L_job_ids_to_retrieve_with_sacct)
    assert L_job_ids_to_retrieve_with_sacct.isdisjoint(L_job_ids_to_insert)

    # print(f"L_job_ids_to_insert: {L_job_ids_to_insert}")
    # print(f"L_job_ids_to_update: {L_job_ids_to_update}")
    # print(f"L_job_ids_to_retrieve_with_sacct: {L_job_ids_to_retrieve_with_sacct}")
    # print(f"DD_jobs_currently_in_mongodb.keys(): {list(DD_jobs_currently_in_mongodb.keys())}")
    # print(f"In main_read_jobs_and_update_collection, there are {len(L_job_ids_to_insert)} jobs to insert for the first time, "
    #     f"{len(L_job_ids_to_update)} to update based on scontrol and {len(L_job_ids_to_retrieve_with_sacct)} to update through sacct."
    # )

    for job_id in L_job_ids_to_update:

        D_job_db = DD_jobs_currently_in_mongodb[job_id]
        D_job_sc = DD_jobs_scontrol[job_id]

        assert D_job_db["slurm"]["cluster_name"] == cluster_name
        assert D_job_sc["slurm"]["cluster_name"] == cluster_name

        # Note that D_job_db has a "_id" which is useful for an update,
        # and it also contains a "user" dict which might have values in it,
        # which is a thing that D_job_sc wouldn't have.

        D_job_new = {}
        for k in ["cw", "slurm", "user"]:
            D_job_new[k] = D_job_db.get(k, {}) | D_job_sc.get(k, {})
        # add this field all the time, whenever you touch an entry
        D_job_new["cw"]["last_slurm_update"] = now
        D_job_new["cw"]["last_slurm_update_by_scontrol"] = now

        L_updates_to_do.append(
            ReplaceOne({"_id": D_job_db["_id"]}, D_job_new, upsert=False)
            # ReplaceOne({"slurm.job_id": D_job_new["slurm"]["job_id"],
            #            "slurm.cluster_name": D_job_new["slurm"]["cluster_name"]},
            # D_job_new, upsert=False)
        )
        append_data_for_dump_file(D_job_new)

    for job_id in L_job_ids_to_insert:
        D_job_sc = DD_jobs_scontrol[job_id]
        # Copy it because it's a bit ugly to start modifying things in place.
        # This can lead to strange interactions with the operations that
        # we want to do with sacct. Might as well keep it clean here.
        D_job_new = copy.copy(D_job_sc)
        # add this field all the time, whenever you touch an entry
        D_job_new["cw"]["last_slurm_update"] = now
        D_job_new["cw"]["last_slurm_update_by_scontrol"] = now
        # No need to the empty user dict because it's done earlier
        # by `slurm_job_to_clockwork_job`.

        L_updates_to_do.append(InsertOne(D_job_new))
        append_data_for_dump_file(D_job_new)

    # Note that we don't want to be running ssh commands with sacct
    # during testing with pytest. This will be possible to manage
    # by specifying `want_sacct=False`.
    if want_sacct and clusters[cluster_name].get("sacct_enabled", False):

        print(
            f"Going to use sacct remotely to {cluster_name} get information about jobs {L_job_ids_to_retrieve_with_sacct}."
        )

        # Fetch the partial job updates with sacct for those jobs that slipped
        # through the cracks.
        LD_sacct_slurm_jobs = fetch_data_with_sacct_on_remote_clusters(
            cluster_name=cluster_name, L_job_ids=L_job_ids_to_retrieve_with_sacct
        )
        print(f"Retrieved information with sacct for {len(LD_sacct_slurm_jobs)} jobs.\n"
            f"len(L_updates_to_do) is {len(L_updates_to_do)} before we process those")

        for D_sacct_slurm_job in LD_sacct_slurm_jobs:

            # There is something very special happening here.
            # It's quite possible that we are dealing with job/task arrays
            # where some of the jobs/tasks are NOT in the original
            # `DD_jobs_currently_in_mongodb`, yet they are present
            # when we call `sacct`. This means that we have to decide
            # whether we'd like to update only the job entries present
            # in `DD_jobs_currently_in_mongodb` (the current choice)
            # or whether we'd like to create minimalist job entries
            # based on the information retrieved by `sacct` (not the current choice).
            
            job_id = D_sacct_slurm_job["jod_id"]
            if job_id in DD_jobs_currently_in_mongodb:
                D_job_db = DD_jobs_currently_in_mongodb[job_id]
                # Note that `D_job_db` has a "_id" which is useful for an update.
                # Moreover, `D_sacct_slurm_job` is just the "slurm" portion,
                # and it's missing most of the fields. It contains only the
                # values that get update when a job finishes running.

                D_job_new = copy.copy(D_job_db)
                del D_job_new["_id"]

                for k in D_sacct_slurm_job:
                    D_job_new["slurm"][k] = D_sacct_slurm_job[k]
                # Add this field all the time, whenever you touch an entry.
                D_job_new["cw"]["last_slurm_update"] = now
                # To keep track of statistics about the need to use sacct.
                D_job_new["cw"]["last_slurm_update_by_sacct"] = now

                L_updates_to_do.append(
                    UpdateOne({"_id": D_job_db["_id"]}, D_job_new, upsert=False)
                    # ReplaceOne({"slurm.job_id": D_job_new["slurm"]["job_id"],
                    #            "slurm.cluster_name": D_job_new["slurm"]["cluster_name"]},
                    #            D_job_new, upsert=False)
                )
                append_data_for_dump_file(D_job_new)
            else:
                # TODO : Print something about the fact that you ignored that job_id.

                # TODO : Decide what to do about updating only jobs present in MongoDB,
                #        even though you know full well that you have let certain jobs slip by.

                pass
        print(f"len(L_updates_to_do) is {len(L_updates_to_do)} after we process those sacct updates")
    else:
        print(
            f"Because of the configuration with sacct_enabled false or missing for {cluster_name}, "
            f"we are NOT going to use sacct get information about jobs {L_job_ids_to_retrieve_with_sacct}."
        )

    # And now for the very rare occasion when we have a user who wants
    # to associate their account on the external cluster (e.g. Compute Canada).

    for D_job in LD_jobs_scontrol:

        # In theory, someone could have copy/pasted the special sbatch command
        # (that we gave them on the web site) on the Mila cluster instead of CC.
        # We really want to avoid that kind of problem whereby someone's
        # "cc_account_username" will be set to their "mila_cluster_username"
        # due to that.
        #
        # The way that we prevent this is by setting a particular value
        # in the cluster config. Here's a snippet from test_config.toml
        # that clearly shows `update_field=false`.
        #    [clusters.mila]
        #    account_field="mila_cluster_username"
        #    update_field=false

        # Register accounts for external clusters (e.g. Compute Canada)
        # using a special comment field in jobs.
        # There is a convention here about the form that
        # a "comment" field can take in order to trigger that.
        comment = D_job["slurm"].get("comment", None)
        marker = "clockwork_register_account:"
        if comment is not None and comment.startswith(marker):
            secret_key = comment[len(marker) :]
            cluster_info = clusters[D_job["slurm"]["cluster_name"]]
            # To help follow along, here's an example of the values
            # taken by those variables in the test_config.toml file.
            #    [clusters.beluga]
            #    account_field = "cc_account_username"
            #    update_field = "cc_account_update_key"
            account_field = cluster_info["account_field"]
            update_field = cluster_info["update_field"]

            # Note that we're looking at entries for "users" here,
            # and not for jobs entries.
            # For users, we have entries in the database that look like this:
            # {
            #   "mila_email_username": "student00@mila.quebec",
            #   "status": "enabled",
            #   "clockwork_api_key": "000aaa00",
            #   "mila_cluster_username": "milauser00",
            #   "cc_account_username": "ccuser00",
            #   "cc_account_update_key": null,
            #   "web_settings": {
            #     "nbr_items_per_page": 40,
            #     "dark_mode": false
            #   },
            #   "personal_picture": "https://mila.quebec/wp-content/uploads/2019/08/guillaume_alain_400x700-400x400.jpg"
            # }

            # The mechanics are as follows.
            # If the `update_field` is present in a job, make note of that username
            # from the job. Then make a query that wants to update the appropriate
            # field for the user in the database that has exactly that secret key.
            if update_field:
                external_username_to_update = D_job["slurm"][account_field]
                L_user_updates.append(
                    UpdateOne(
                        {update_field: secret_key},
                        {
                            "$set": {
                                account_field: external_username_to_update,
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
            print("users_collection.bulk_write(L_user_updates, upsert=False)")
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

    now = time.time()

    for D_node in map(
        slurm_node_to_clockwork_node,
        fetch_slurm_report_nodes(cluster_desc_path, scontrol_show_node_path),
    ):

        # add this field all the time, whenever you touch an entry
        D_node["cw"]["last_slurm_update"] = now

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

        # This is all useless. It's a copy/paste of the things we do
        # for jobs, and it's not necessary for nodes because we don't
        # have the "user" field that we want to avoid overwriting.
        # We can reactivate this later if we ever get such a field.

        # Here we can add set extra values to "cw".
        # L_updates_to_do.append(
        #    UpdateOne(
        #        # rule to match if already present in collection
        #        {
        #            "slurm.name": D_node["slurm"]["name"],
        #            "slurm.cluster_name": D_node["slurm"]["cluster_name"],
        #        },
        #        # the data that we write in the collection
        #        {"$set": {"cw.last_slurm_update": now}},
        #        # don't create if missing, update if present
        #        upsert=False,
        #    )
        # )

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
