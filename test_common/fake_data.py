"""
Utilities to prepare fake data for tests.
"""


import pytest
import os
import json


@pytest.fixture
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
    return E


def populate_fake_data(db_insertion_point, json_file=None):
    """
    This json file should contain a dict with keys "users", "jobs", "nodes".
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

    for k in ["users", "jobs", "nodes", "gpu"]:
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
