
from flask import current_app

import pytest
from clockwork_web.db import get_db, init_db

def test_insert_and_retrieve(app):
    with app.app_context():
        mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]

        job_id = 4872438  # just a meaningless random number
        # delete any remaining elements from a previous test first
        mc["jobs"].delete_many({"job_id": job_id})

        mc["jobs"].insert_one({"cluster_name": "mila", "job_id": job_id})
        L = list(mc["jobs"].find({"job_id": job_id}))
        assert len(L) == 1
        assert L[0]["job_id"] == job_id
        assert L[0]["cluster_name"] == "mila"

        # clean up
        mc["jobs"].delete_many({"job_id": job_id})
