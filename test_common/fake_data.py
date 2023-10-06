"""
Utilities to prepare fake data for tests.
"""


import pytest
import os
import json


@pytest.fixture(scope="session")
def fake_data():
    """
    The genius of having `fake_data` as fixture is that all those tests that depend
    on verifying some fake data in the database can now be written in a way that
    can adjust automatically to updates in the "fake_data.json" file.
    """
    json_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fake_data.json"
    )
    with open(json_file, "r") as f:
        E = json.load(f)
    mutate_some_job_status(E)
    return E


def populate_fake_data(db_insertion_point, json_file=None, mutate=False):
    """
    This json file should contain a dict with keys "users", "jobs", "nodes" and "gpu".
    Not all those keys need to be present. If they are,
    then we will update the corresponding collections in the database.

    `db_insertion_point` is something like db["clockwork"],
    at the level right before which we specify the collection.
    It's hard to find the right word for this, because mongodb would
    call it a "database", but in the context of this flask app we refer
    to the database connection as the "db".

    This function returns its own cleanup function that will remove
    all the entries that it has inserted. You can call it to undo
    the side-effects, and hopefully there won't be any conflict with
    real values of job_id and those fake ones.
    """

    if json_file is None:
        json_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fake_data.json"
        )
    assert os.path.exists(
        json_file
    ), f"Failed to find the fake data file to populate the database for testing: {json_file}."
    with open(json_file, "r") as f:
        E = json.load(f)

    if mutate:
        mutate_some_job_status(E)

    # Create indices. This isn't half as important as when we're
    # dealing with large quantities of data, but it's part of the
    # set up for the database.
    db_insertion_point["jobs"].create_index(
        [("slurm.job_id", 1), ("slurm.cluster_name", 1)],
        name="job_id_and_cluster_name",
    )
    db_insertion_point["nodes"].create_index(
        [("slurm.name", 1), ("slurm.cluster_name", 1)],
        name="name_and_cluster_name",
    )
    db_insertion_point["users"].create_index(
        [("mila_email_username", 1)], name="users_email_index"
    )
    db_insertion_point["gpu"].create_index([("name", 1)], name="gpu_name")
    db_insertion_point["labels"].create_index([("user_id", 1), ("job_id", 1)], name="user_id_and_job_id")

    for k in ["users", "jobs", "nodes", "gpu", "labels"]:
        if k in E:
            for e in E[k]:
                db_insertion_point[k].insert_one(e)

    def cleanup_function():
        """
        Each of those kinds of data is identified in a unique way,
        and we can use that identifier to clean up.

        For example, when clearing out jobs, we can look at the "job_id"
        of the entries that we inserted.

        The point is that we can run a test against the production mongodb on Atlas
        and not affect the real data. If we cleared the tables completely,
        then we'd be affecting the real data in a bad way.
        """
        for e in E["users"]:
            db_insertion_point["users"].delete_many(
                {"mila_email_username": e["mila_email_username"]}
            )

        for e in E["gpu"]:
            db_insertion_point["gpu"].delete_many({"name": e["name"]})

        for (k, sub, id_field) in [
            ("jobs", "slurm", "job_id"),
            ("nodes", "slurm", "name"),
        ]:
            if k in E:
                for e in E[k]:
                    # This is complicated, but it's just about a way to say something like
                    # that we want to remove {"slurm.job_id", e["slurm"]["job_id"]},
                    # and the weird notation comes from the fact that mongodb filters use dots,
                    # but not the original python.
                    db_insertion_point[k].delete_many(
                        {f"{sub}.{id_field}": e[sub][id_field]}
                    )

    return cleanup_function


# Map from job state to aggregated
# CAUTION: this is a copy/paste from clockwork_web.core.jobs_helper,
# do not modify without modifying the other copy.
job_state_to_aggregated = {
    "BOOT_FAIL": "FAILED",
    "CANCELLED": "FAILED",
    "COMPLETED": "COMPLETED",
    "CONFIGURING": "PENDING",
    "COMPLETING": "RUNNING",
    "DEADLINE": "FAILED",
    "FAILED": "FAILED",
    "NODE_FAIL": "FAILED",
    "OUT_OF_MEMORY": "FAILED",
    "PENDING": "PENDING",
    "PREEMPTED": "FAILED",
    "RUNNING": "RUNNING",
    "RESV_DEL_HOLD": "PENDING",
    "REQUEUE_FED": "PENDING",
    "REQUEUE_HOLD": "PENDING",
    "REQUEUED": "PENDING",
    "RESIZING": "PENDING",
    "REVOKED": "FAILED",
    "SIGNALING": "RUNNING",
    "SPECIAL_EXIT": "FAILED",
    "STAGE_OUT": "RUNNING",
    "STOPPED": "FAILED",
    "SUSPENDED": "FAILED",
    "TIMEOUT": "FAILED",
}


# Relative proportions of jobs for each job state
status_counts = {
    "BOOT_FAIL": 1,
    "CANCELLED": 1,
    "COMPLETED": 10,
    "CONFIGURING": 1,
    "COMPLETING": 1,
    "DEADLINE": 1,
    "FAILED": 10,
    "NODE_FAIL": 1,
    "OUT_OF_MEMORY": 1,
    "PENDING": 10,
    "PREEMPTED": 1,
    "RUNNING": 20,
    "RESV_DEL_HOLD": 1,
    "REQUEUE_FED": 1,
    "REQUEUE_HOLD": 1,
    "REQUEUED": 1,
    "RESIZING": 1,
    "REVOKED": 1,
    "SIGNALING": 1,
    "SPECIAL_EXIT": 1,
    "STAGE_OUT": 1,
    "STOPPED": 1,
    "SUSPENDED": 1,
    "TIMEOUT": 1,
}


def mutate_some_job_status(data):
    """
    Mutates all job statuses to match a certain distribution. The start_time,
    end_time and nodes fields are made coherent with the rest.
    """
    L_status = []
    for status, n in status_counts.items():
        L_status += [status] * n

    nodes = data["nodes"]

    for (i, job) in enumerate(data["jobs"]):
        slurm = job["slurm"]
        job_state = L_status[i % len(L_status)]
        slurm["job_state"] = job_state
        agg = job_state_to_aggregated[job_state]

        if agg == "PENDING":
            slurm["start_time"] = None
            slurm["nodes"] = None

        if agg in ("PENDING", "RUNNING"):
            slurm["end_time"] = None

        if agg in ("RUNNING", "COMPLETED", "FAILED"):
            if not slurm["start_time"]:
                slurm["start_time"] = slurm["submit_time"]
            if not slurm["nodes"]:
                slurm["nodes"] = nodes[i % len(nodes)]["slurm"]["name"]

        if agg in ("COMPLETED", "FAILED"):
            if not slurm["end_time"]:
                slurm["end_time"] = slurm["start_time"] + 7200  # 2 hours
