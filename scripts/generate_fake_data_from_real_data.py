"""
To test the app, we want to use fake data.
The easiest way to generate such fake data is to use the system
that's already running and to pull real data from mongodb.
We can anonymize it and then save it to a json file.

This might seem like a chicken-and-egg situation,
but we're already in a situation where we have such
a system running so we might as well use it.

Moreover, if we want to generate new fake data later on,
we can fetch the data from our database at that point.
This means that the data generate will always be a fair
representation of the current format of the data.
"""

import numpy as np
import os
import json
from pymongo import MongoClient
from datetime import datetime


def fix_job(D_job: dict):
    """
    Mostly about anonymization.
    Mutates the argument `D_job`.
    """

    fake_username = np.random.choice(["mario", "luigi", "peach", "toad"])

    # scrub those fields because they contain identifiable information
    L_fields_to_wipe = [
        "command",
        "comment",
        "name",
        "std_err",
        "std_in",
        "std_out",
        "work_dir",
        "account",
    ]
    for field_to_wipe in L_fields_to_wipe:
        if field_to_wipe in D_job:
            D_job[field_to_wipe] = "anonymized_for_fake_data"

    L_name_fields = [
        "cc_account_username",
        "mila_email_username",
        "mila_cluster_username",
        "mila_user_account",
    ]
    for name_field in L_name_fields:
        # let's just replace the fields that are not "unknown"
        if D_job.get(name_field, "unknown") != "unknown":
            D_job[name_field] = fake_username


def fix_node(D_node: dict):
    """
    It's not clear what needs to be anonymized in this case.
    Maybe just the "os" field because it reveals information
    to the public about the particular version that could be
    out of date.

    Mutates the `D_node` argument.
    """
    L_fields_to_wipe = ["os"]
    for field_to_wipe in L_fields_to_wipe:
        if field_to_wipe in D_node:
            D_node[field_to_wipe] = "anonymized_for_fake_data"


def main():

    mc = MongoClient(os.environ["CLOCKWORK_MONGODB_DATABASE"])["slurm"]

    nbr_max_jobs_per_category = 4
    LD_jobs = []
    for cluster_name in ["mila", "beluga", "graham", "cedar"]:
        for job_state in ["RUNNING", "PENDING", "COMPLETED", "FAILED"]:
            for (k, D_job) in enumerate(
                mc["jobs"].find({"cluster_name": cluster_name, "job_state": job_state})
            ):
                if k >= nbr_max_jobs_per_category:
                    break
                else:
                    del D_job["_id"]  # clear this "_id" field coming from mongodb
                    if "licenses" in D_job:
                        del D_job["licenses"]  # this is an Object
                    # mongodb stores certain things as a datetime object,
                    # but we can't put that in a json
                    if "timestamp" in D_job and isinstance(
                        D_job["timestamp"], datetime
                    ):
                        D_job["timestamp"] = D_job["timestamp"].timestamp()

                    fix_job(D_job)  # mutates D_job
                    LD_jobs.append(D_job)

    nbr_max_nodes_per_category = 10
    LD_nodes = []
    for cluster_name in ["mila", "beluga", "graham", "cedar"]:
        for (k, D_node) in enumerate(mc["nodes"].find({"cluster_name": cluster_name})):
            if k >= nbr_max_nodes_per_category:
                break
            else:
                del D_node["_id"]  # clear this "_id" field coming from mongodb
                # mongodb stores certain things as a datetime object,
                # but we can't put that in a json
                if "timestamp" in D_node and isinstance(D_node["timestamp"], datetime):
                    D_node["timestamp"] = D_node["timestamp"].timestamp()
                fix_node(D_node)  # mutates D_node
                LD_nodes.append(D_node)

    LD_users = [
        {
            "id": "%0.6d" % np.random.randint(low=0, high=10000),
            "name": name,
            "email": "%s@mila.quebec" % name,
            "profile_pic": "",
            "status": "enabled",
            "clockwork_api_key": "000aaa",
        }
        for name in ["mario", "luigi", "peach", "toad"]
    ]

    for D_node in LD_nodes:
        for (k, v) in D_node.items():
            if isinstance(v, datetime):
                print((k, v))
                quit()

    # the whole point is to write this fake data to a file
    with open("fake_data.json", "w") as f:
        json.dump({"users": LD_users, "jobs": LD_jobs, "nodes": LD_nodes}, f, indent=4)


if __name__ == "__main__":
    main()


# {$and: [{"job_state": {$ne: "COMPLETED"}}, {"job_state": {$ne: "PENDING"}}, {"job_state": {$ne: "RUNNING"}}]}
