import os, time
import numpy as np
from mongo_client import get_mongo_client
from pymongo import UpdateOne
import json
import zoneinfo

from scontrol_parser import job_parser, node_parser

def fetch_slurm_report_jobs(cluster_desc_path, scontrol_report_path):
    return _fetch_slurm_report_helper(job_parser, cluster_desc_path, scontrol_report_path)

def fetch_slurm_report_nodes(cluster_desc_path, scontrol_report_path):
    return _fetch_slurm_report_helper(node_parser, cluster_desc_path, scontrol_report_path)

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
        ctx_beluga = json.load(f)
        ctx_beluga["timezone"] = zoneinfo.ZoneInfo(ctx_beluga["timezone"])

    with open(scontrol_report_path, "r") as f:
        for e in parser(f, ctx_beluga):
            e["cluster_name"] = ctx_beluga["name"]
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

# def none_string_to_none_object(D:dict):
#     """
#     Returns a new dict with the same content
#     as the `D` argument, but whenever a key is '(null)'
#     it is turned into a `None` object instead.
#     """
#     return dict( ((k, None) if v == '(null)' else (k, v)) for (k, v) in D.items() )


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
        "cw": {
        },
    }
    return clockwork_node


def main_read_jobs_and_update_collection(
    jobs_collection,
    cluster_desc_path,
    scontrol_show_job_path):

    # What we want is to create the entry as
    #    {"slurm": slurm_dict, "cw": cw_dict, "user": user_dict}
    # if it's not present in the database,
    # but if it actually is already there then we only want
    # to update the "slurm" part of it.

    # Note that adding an extra {"$set": {"cw.last_slurm_update": time.time()}}
    # after the $setOnInsert operator does not work with mongodb.

    timestamp_start = time.time()
    L_updates_to_do = []

    for (n, D_job) in enumerate(
        map(
            infer_user_accounts,
            map(
                slurm_job_to_clockwork_job,
                    fetch_slurm_report_jobs(cluster_desc_path, scontrol_show_job_path)
            ),
        )
    ):
        # if 4 <= n:
        #    break
        if n < 2:
            print(D_job)

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

    result = jobs_collection.bulk_write(L_updates_to_do)  #  <- the actual work
    # print(result.bulk_api_result)
    mongo_update_duration = time.time() - timestamp_start
    print(
        f"Bulk write for {len(L_updates_to_do)} job entries in mongodb took {mongo_update_duration} seconds."
    )



def main_read_nodes_and_update_collection(
    nodes_collection,
    cluster_desc_path,
    scontrol_show_node_path):

    # What we want is to create the entry as
    #    {"slurm": slurm_dict, "cw": cw_dict}
    # if it's not present in the database,
    # but if it actually is already there then we only want
    # to update the "slurm" part of it.

    timestamp_start = time.time()
    L_updates_to_do = []

    for (n, D_node) in enumerate(
        map(
            slurm_node_to_clockwork_node,
                fetch_slurm_report_nodes(cluster_desc_path, scontrol_show_node_path)
        ),
    ):
        # if 4 <= n:
        #    break
        if n < 2:
            print(D_node)

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

    result = nodes_collection.bulk_write(L_updates_to_do)  #  <- the actual work
    # print(result.bulk_api_result)
    mongo_update_duration = time.time() - timestamp_start
    print(
        f"Bulk write for {len(L_updates_to_do)} node entries in mongodb took {mongo_update_duration} seconds."
    )


def run():
    """
    This function is never going to be called in production.
    It's there mostly to test this script without going through
    "read_report_commit_to_db.py".
    """

    connection_string = os.environ.get("MONGODB_CONNECTION_STRING", "")
    assert connection_string
    client = get_mongo_client(connection_string)

    database_name = os.environ.get("MONGODB_DATABASE_NAME", "")
    assert database_name


    # https://stackoverflow.com/questions/33541290/how-can-i-create-an-index-with-pymongo
    # Apparently "ensure_index" is deprecated, and we should always call "create_index".
    timestamp_start = time.time()
    client[database_name]["nodes"].create_index(
        [("slurm.name", 1), ("slurm.cluster_name", 1)], name="name_and_cluster_name"
    )
    client[database_name]["jobs"].create_index(
        [("slurm.job_id", 1), ("slurm.cluster_name", 1)], name="job_id_and_cluster_name"
    )
    create_index_duration = time.time() - timestamp_start
    print(f"create_index took {create_index_duration} seconds.")


    # Now let's do both nodes and jobs, with hardcoded paths.

    for (cluster_desc_path, scontrol_show_node_path) in [
        ("./cluster_desc/mila.json", "../tmp/slurm_report/mila/scontrol_show_node"),
        ("./cluster_desc/beluga.json", "../tmp/slurm_report/beluga/scontrol_show_node"),
        ("./cluster_desc/cedar.json", "../tmp/slurm_report/cedar/scontrol_show_node"),
        ("./cluster_desc/graham.json", "../tmp/slurm_report/graham/scontrol_show_node"),
    ]:
        main_read_nodes_and_update_collection(
            client[database_name]["nodes"],
            cluster_desc_path, scontrol_show_node_path)

    for (cluster_desc_path, scontrol_show_job_path) in [
        ("./cluster_desc/mila.json", "../tmp/slurm_report/mila/scontrol_show_job"),
        ("./cluster_desc/beluga.json", "../tmp/slurm_report/beluga/scontrol_show_job"),
        # ("./cluster_desc/cedar.json", "../tmp/slurm_report/cedar/scontrol_show_job"),
        ("./cluster_desc/graham.json", "../tmp/slurm_report/graham/scontrol_show_job"),
    ]:
        main_read_jobs_and_update_collection(
            client[database_name]["jobs"],
            cluster_desc_path, scontrol_show_job_path)




if __name__ == "__main__":
    run()


"""
export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@127.0.0.1:37017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"

docker-compose -f setup_ecosystem/docker-compose.yml run --service-ports mongodb


"""
