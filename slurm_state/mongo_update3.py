import os, time
import numpy as np
from mongo_client import get_mongo_client
from pymongo import UpdateOne
import json
import zoneinfo

from scontrol_parser import job_parser, node_parser


def fake_job_entries(N):
    for n in range(N):
        yield {
            "slurm": {
                "cc_account_username": "tommy",
                "job_state": "RUNNING",
                "cluster_name": "beluga",
                "job_id": str(np.random.randint(low=0, high=1e6)),
                # "job_id": np.random.randint(low=0, high=1e6),
                "command": None,
            },
            "cw": {
                "cc_account_username": "tommy",
                "mila_account_username": "enginet",
                "mila_email_username": "thomas.engine",
            },
            "user": {"blastoise": True},
        }


def fetch_slurm_report_jobs(cluster_desc_path, scontrol_show_job_path):
    """
    
    Yields elements ready to be slotted into the "slurm" field,
    but they have to be processed further before committing to mongodb.
    """

    assert os.path.exists(cluster_desc_path), (
        f"cluster_desc_path {cluster_desc_path} is missing.")
    assert os.path.exists(scontrol_show_job_path), (
        f"scontrol_show_job_path {scontrol_show_job_path} is missing.")

    class CTX:
        pass

    with open(cluster_desc_path, "r") as f:
        E = json.load(f)
        ctx_beluga = CTX()
        for (k, v) in E.items():
            if k in ["timezone"]:
                pass
            setattr(ctx_beluga, k, v)
        setattr(ctx_beluga, "timezone", zoneinfo.ZoneInfo(E["timezone"]))

    with open(scontrol_show_job_path, "r") as f:
        for e in job_parser(f, ctx_beluga):
            # hardcode that one because it's not being added at the moment
            # in the functions from scontrol_parser.py (TODO : ask Arnaud about it)
            e["cluster_name"] = ctx_beluga.name
            yield e


def slurm_job_to_clockwork_job(slurm_job:dict):
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
        }, "user": {}}
    infer_user_accounts(clockwork_job)  # mutates argument
    return clockwork_job


def infer_user_accounts(clockwork_job:dict[dict]):
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


def run():

    connection_string = os.environ.get("MONGODB_CONNECTION_STRING", "")
    assert connection_string
    client = get_mongo_client(connection_string)

    database_name = os.environ.get("MONGODB_DATABASE_NAME", "")
    assert database_name

    # What we want is to create the entry as
    #    {"slurm": slurm_dict, "cw": cw_dict, "user": user_dict}
    # if it's not present in the database,
    # but if it actually is already there then we only want
    # to update the "slurm" part of it.

    # Maybe we should add an extra {"$set": {"cw.last_slurm_update": time.time()}}
    # after the $setOnInsert operator. This does not work with mongodb.

    for (cluster_desc_path, scontrol_show_job_path) in [
        ("./cluster_desc/mila.json", "../tmp/slurm_report/mila/scontrol_show_job"),
        ("./cluster_desc/beluga.json", "../tmp/slurm_report/beluga/scontrol_show_job"),
        ("./cluster_desc/cedar.json", "../tmp/slurm_report/cedar/scontrol_show_job"),
        ("./cluster_desc/graham.json", "../tmp/slurm_report/graham/scontrol_show_job"),
        ]:

        timestamp_start = time.time()
        L_updates_to_do = []

        for (n, D_job) in enumerate(
            map(infer_user_accounts,
                map(slurm_job_to_clockwork_job,
                    fetch_slurm_report_jobs(cluster_desc_path, scontrol_show_job_path)))):
            if 4 <= n:
                break
            print(D_job)

            L_updates_to_do.append(
                UpdateOne(
                    # rule to match if already present in collection
                    {
                        "slurm.job_id": D_job["slurm"]["job_id"],
                        "slurm.cluster_name": D_job["slurm"]["cluster_name"],
                    },
                    # the data that we write in the collection
                    # {"$set": D_job["slurm"]},
                    {
                        "$set": {"slurm": D_job["slurm"]},
                        # "job_id": D_job["slurm"]["job_id"],
                        # "cluster_name": D_job["slurm"]["cluster_name"]},
                        "$setOnInsert": {"cw": D_job["cw"], "user": D_job["user"]},
                    },
                    # create if missing, update if present
                    upsert=True,
                ))

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
                ))

        # this is a one-liner, but we're breaking it into multiple steps to highlight the structure
        database = client[database_name]
        jobs_collection = database["jobs"]
        result = jobs_collection.bulk_write(L_updates_to_do)  #  <- the actual work
        # print(result.bulk_api_result)
        mongo_update_duration = time.time() - timestamp_start
        print(
            f"Bulk write for {len(L_updates_to_do)} job entries in mongodb took {mongo_update_duration} seconds."
        )


if __name__ == "__main__":
    run()


"""
export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@127.0.0.1:37017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"

docker-compose -f setup_ecosystem/docker-compose.yml run --service-ports mongodb


"""
