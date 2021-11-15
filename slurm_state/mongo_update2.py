import os, time
import numpy as np
from mongo_client import get_mongo_client
from pymongo import UpdateOne


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

    LD_jobs = list(fake_job_entries(N=1000))

    for i in range(2):

        timestamp_start = time.time()

        L_updates_to_do = [
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
            )
            for D_job in LD_jobs
        ]

        # Here we can add set extra values to "cw".
        for D_job in LD_jobs:
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
    for _ in range(50):
        run()

"""
export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@127.0.0.1:37017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"

docker-compose -f setup_ecosystem/docker-compose.yml run --service-ports mongodb


"""
