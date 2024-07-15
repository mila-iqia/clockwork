from flask import current_app

import pytest
from clockwork_web.db import get_db, init_db


def test_insert_and_retrieve(app):
    """
    This tests the connection to the database,
    but not the functionality of the web server.
    """

    with app.app_context():
        mc = get_db()

        job_id = 4872438  # just a meaningless random number
        # delete any remaining elements from a previous test first
        mc["jobs"].delete_many({"slurm.job_id": job_id, "slurm.cluster_name": "mila"})

        mc["jobs"].insert_one(
            {"slurm": {"cluster_name": "mila", "job_id": job_id}, "cw": {}}
        )
        L = list(
            mc["jobs"].find({"slurm.job_id": job_id, "slurm.cluster_name": "mila"})
        )
        assert len(L) == 1
        assert L[0]["slurm"]["job_id"] == job_id
        assert L[0]["slurm"]["cluster_name"] == "mila"

        # clean up
        mc["jobs"].delete_many({"slurm.job_id": job_id, "slurm.cluster_name": "mila"})
