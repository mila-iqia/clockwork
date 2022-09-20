"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import os
import time
from pprint import pprint
import random
import json
import pytest
from clockwork_web.db import get_db
from clockwork_web.config import get_config
from test_common.jobs_test_helpers import (
    helper_list_relative_time,
    helper_single_job_missing,
    helper_single_job_at_random,
    helper_list_jobs_for_a_given_random_user,
    helper_jobs_list_with_filter,
)


@pytest.mark.parametrize("cluster_name", ("mila", "beluga", "cedar", "graham"))
def test_single_job_at_random(client, fake_data, valid_rest_auth_headers, cluster_name):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/one.

    This job entry should be present in the database.
    We test for every database just to be sure that we get jobs
    corresponding to the data format used by each scraping method
    (i.e. when PySlurm works at one place but not the other, it's worth
    making sure that job_id stored as int vs strings doesn't cause issues).
    """

    validator, job_id = helper_single_job_at_random(fake_data, cluster_name)

    response = client.get(
        f"/api/v1/clusters/jobs/one?job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert "application/json" in response.content_type
    D_job = response.json
    validator(D_job)


def test_single_job_missing(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/one.

    This job entry should be missing from the database.
    """

    validator, job_id = helper_single_job_missing(fake_data)
    response = client.get(
        f"/api/v1/clusters/jobs/one?job_id={job_id}", headers=valid_rest_auth_headers
    )
    assert "application/json" in response.content_type
    D_job = response.json  # no `json()` here, just `json`
    validator(D_job)


def test_single_job_no_id(client, valid_rest_auth_headers):
    response = client.get("/api/v1/clusters/jobs/one", headers=valid_rest_auth_headers)
    assert response.status_code == 400


def test_list_jobs_for_a_given_random_user(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.

    Note that the users for whom we list the jobs is probably not
    going to be the user encoded in the auth_headers, which we get
    from the configuration variables "clockwork.test.email"
    and "clockwork.test.api_key".

    We pick a user at random from our fake_data, and we see if we
    can list the jobs for that user.
    """

    validator, username = helper_list_jobs_for_a_given_random_user(fake_data)

    response = client.get(
        f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers
    )
    assert response.content_type == "application/json"
    LD_jobs = response.get_json()
    validator(LD_jobs)


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_api_list_invalid_username(client, valid_rest_auth_headers, username):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
    """
    response = client.get(
        f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers
    )
    assert response.content_type == "application/json"
    LD_jobs = response.get_json()

    # we expect no matches for those made-up names
    assert len(LD_jobs) == 0


def test_api_list_invalid_relative_time(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
    """
    response = client.get(
        f"/api/v1/clusters/jobs/list?relative_time=this_is_not_a_valid_relative_time",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 400  # bad request
    error_msg = response.get_json()

    assert (
        "Field 'relative_time' cannot be cast as a valid float: this_is_not_a_valid_relative_time."
        in error_msg
    )


def test_api_list_relative_time(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
    """

    validator, relative_mid_end_time = helper_list_relative_time(fake_data)

    response = client.get(
        f"/api/v1/clusters/jobs/list?relative_time={relative_mid_end_time}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    LD_jobs_results = response.get_json()
    validator(LD_jobs_results)


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth")
)
def test_jobs_list_with_filter(
    client, fake_data, valid_rest_auth_headers, cluster_name
):
    """
    Test the `jobs_list` command. This is just to make sure that the filtering works
    and the `cluster_name` argument is functional.

    Note that "sephiroth" is not a valid cluster, so we will expect empty lists as results.
    """
    validator = helper_jobs_list_with_filter(fake_data, cluster_name=cluster_name)
    response = client.get(
        f"/api/v1/clusters/jobs/list?cluster_name={cluster_name}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    LD_jobs_results = response.get_json()
    validator(LD_jobs_results)


@pytest.mark.parametrize("cluster_name", ("mila", "cedar", "graham", "beluga"))
@pytest.mark.parametrize("update_allowed", (True, False))
def test_jobs_user_dict_update_successful_update(
    app, client, fake_data, valid_rest_auth_headers, cluster_name, update_allowed
):
    """
    Test the `user_dict_update` command with a successful update.

    """

    with app.app_context():
        mc = get_db()

        # retrieve the user in the database in order to know its three usernames
        LD_users = list(
            mc["users"].find(
                {"mila_email_username": get_config("clockwork.test.email")}
            )
        )
        assert len(LD_users) == 1
        D_user = LD_users[0]

        # it so happens that the "test user" doesn't have any job on the mila cluster
        # so we'll just bypass all of that by insert new jobs
        D_updates_to_user_dict = {
            "nbr_dinosaurs": 10,
            "train_loss": 0.23,
            "test_loss": 0.40,
            "experiment_name": "save the planet",
        }

        D_job = {
            "slurm": {
                "job_id": str(int(random.random() * 1e8)),
                "cluster_name": cluster_name,
            },
            "cw": {
                "cc_account_username": None,
                "mila_cluster_username": None,
                "mila_email_username": None,
            },
            "user": {
                "nbr_dinosaurs": 0,  # some field that will be updated
                "to_be_left_untouched": "can't touch this",
            },
        }
        if cluster_name in ["cedar", "graham", "beluga", "narval"]:
            if update_allowed:
                D_job["cw"]["cc_account_username"] = D_user["cc_account_username"]
            else:
                D_job["cw"]["cc_account_username"] = (
                    "NOT_" + D_user["cc_account_username"]
                )
        elif cluster_name in ["mila"]:
            if update_allowed:
                D_job["cw"]["mila_cluster_username"] = D_user["mila_cluster_username"]
            else:
                D_job["cw"]["mila_cluster_username"] = (
                    "NOT_" + D_user["mila_cluster_username"]
                )
        else:
            raise Exception("You're not handling properly the cluster_name parameter.")

        mc["jobs"].insert_one(D_job)

        response = client.put(
            "/api/v1/clusters/jobs/user_dict_update",
            data={
                "job_id": D_job["slurm"]["job_id"],
                "cluster_name": D_job["slurm"]["cluster_name"],
                "update_pairs": json.dumps(D_updates_to_user_dict),
            },
            headers=valid_rest_auth_headers,
        )
        assert response.content_type == "application/json"
        if update_allowed:
            print(response.json)
            assert response.status_code == 200
            # Now check that our update was done properly.
            L = list(
                mc["jobs"].find(
                    {
                        "slurm.job_id": D_job["slurm"]["job_id"],
                        "slurm.cluster_name": D_job["slurm"]["cluster_name"],
                    }
                )
            )
            assert len(L) == 1, f"We should have one entry but we have {len(L)}."
            D_job_retrieved = L[0]
            # Check that all the keys in the "user" field are indeed updated.
            for (k, v) in D_updates_to_user_dict.items():
                assert D_job_retrieved["user"][k] == v
            # That value should not have been updated.
            assert (
                D_job_retrieved["user"]["to_be_left_untouched"]
                == D_job["user"]["to_be_left_untouched"]
            )
        else:
            assert response.status_code == 403

        # Note that we haven't tested for a 404 error when the job doesn't exist.

        # cleanup after your test
        mc["jobs"].delete_many({"slurm.job_id": D_job["slurm"]["job_id"]})
