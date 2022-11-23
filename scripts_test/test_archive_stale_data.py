"""
Tests that the script to archive stale data actually works,
that it saves the contents to a file as promised, and that
it deletes the stale contents from the database.
"""

from pymongo import MongoClient

# import pytest
from scripts import archive_stale_data
from scripts_test.config import get_config

import json
import numpy as np
import tempfile
import time


def test_archive_stale_data():
    """ """

    # Pick something unique that we don't care about, because we're going
    # to mess around with the "jobs" and "nodes" collections.
    database_name = "stale_data_48723mds"

    # Connect to MongoDB
    client = MongoClient(get_config("mongo.connection_string"))
    mc = client[database_name]

    now = time.time()
    days_since_last_update = 30
    seconds_since_last_update = days_since_last_update * 24 * 60 * 60

    def get_random_timestamp():
        """
        Because time flows and by the time we call `archive_stale_data.archive`
        the value of `time.time()` will be different, we don't want values that
        are too close to being stale. Let's try to create a gap of some sorts.
        """
        if np.random.rand() < 0.5:
            return float(
                int(
                    (now - seconds_since_last_update)
                    - 1000 * (1 + np.random.randn() ** 2)
                )
            )
        else:
            return float(
                int(
                    (now - seconds_since_last_update)
                    + 1000 * (1 + np.random.randn() ** 2)
                )
            )

    ########
    # Jobs #
    ########

    nbr_jobs = 10
    # We will insert those in the database to prepare our query.
    LD_jobs = [
        {
            "cw": {"last_slurm_update": get_random_timestamp()},
            "slurm": {
                "cluster_name": "mila",
                "job_id": f"{np.random.randint(low=0, high=1e6)}",
            },
        }
        for _ in range(nbr_jobs)
    ]
    mc["jobs"].delete_many({})
    mc["jobs"].insert_many(LD_jobs, ordered=False)
    # because pymongo mutates `LD_jobs`` to add that "_id"
    for D_job in LD_jobs:
        del D_job["_id"]

    # These are the ground truth against which we will test the returned values.
    LD_stale_jobs = [
        D_job
        for D_job in LD_jobs
        if (D_job["cw"]["last_slurm_update"] < now - seconds_since_last_update)
    ]
    LD_fresh_jobs = [
        D_job
        for D_job in LD_jobs
        if (D_job["cw"]["last_slurm_update"] >= now - seconds_since_last_update)
    ]

    #########
    # Nodes #
    #########

    nbr_nodes = 10
    # We will insert those in the database to prepare our query.
    LD_nodes = [
        {
            "cw": {"last_slurm_update": get_random_timestamp()},
            "slurm": {
                "cluster_name": "mila",
                "name": f"some_node_name_{np.random.randint(low=0, high=1e3)}",
            },
        }
        for _ in range(nbr_nodes)
    ]
    mc["nodes"].delete_many({})
    mc["nodes"].insert_many(LD_nodes, ordered=False)
    # because pymongo mutates `LD_nodes`` to add that "_id"
    for D_node in LD_nodes:
        del D_node["_id"]

    # These are the ground truth against which we will test the returned values.
    LD_stale_nodes = [
        D_node
        for D_node in LD_nodes
        if (D_node["cw"]["last_slurm_update"] < now - seconds_since_last_update)
    ]
    LD_fresh_nodes = [
        D_node
        for D_node in LD_nodes
        if (D_node["cw"]["last_slurm_update"] >= now - seconds_since_last_update)
    ]

    # We're going to have the contents archived to a JSON file, but also returned
    # by the function call. We can compare all that. If we didn't care about the JSON,
    # we wouldn't be doing this `NamedTemporaryFile` approach.

    with tempfile.NamedTemporaryFile(mode="w", dir=None, delete=False) as f_out:
        # remember the name because you're going to read it later
        archive_path = f_out.name

        contents_archived_0 = archive_stale_data.archive(
            archive_path, database_name, days_since_last_update
        )

    with open(archive_path, "r") as f_in:
        contents_archived_1 = json.load(f_in)

    def sorted_by_last_update(E):
        """
        We don't want to have to deal with a mess comparing lists
        in different orders, so we'll just have this helper function
        to reorganize the elements by value of "last_slurm_update"
        since those are unique.
        """
        if isinstance(E, list):

            def f(D):
                # get some id that works for jobs and nodes to break ties with equal `last_slurm_update`
                id = D["slurm"].get("job_id", D["slurm"].get("name", None))
                return (D["cw"]["last_slurm_update"], id)

            return list(sorted(E, key=f))
        elif isinstance(E, dict):
            # we expect "jobs" and "nodes" in there only
            return dict((k, sorted_by_last_update(v)) for (k, v) in E.items())

    # Almost trival verification, more of a validation that `json.dump`
    # is indeed being called inside of `archive_stale_data.archive`.
    assert sorted_by_last_update(contents_archived_0) == sorted_by_last_update(
        contents_archived_1
    )

    # Validate that the archived contents is the old stuff.
    assert sorted_by_last_update(
        {"jobs": LD_stale_jobs, "nodes": LD_stale_nodes}
    ) == sorted_by_last_update(contents_archived_1)

    # Validate that the fresh stuff is still in the database.
    LD_jobs_still_in_database = list(mc["jobs"].find({}))
    for D in LD_jobs_still_in_database:
        del D["_id"]
    #
    LD_nodes_still_in_database = list(mc["nodes"].find({}))
    for D in LD_nodes_still_in_database:
        del D["_id"]
    #
    assert sorted_by_last_update(LD_jobs_still_in_database) == sorted_by_last_update(
        LD_fresh_jobs
    )
    assert sorted_by_last_update(LD_nodes_still_in_database) == sorted_by_last_update(
        LD_fresh_nodes
    )

    # clean up (not really necessary)
    mc["jobs"].delete_many({})
    mc["nodes"].delete_many({})