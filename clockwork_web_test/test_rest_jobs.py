
"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import json
import pytest


def test_single_job_1000922(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/cluster/jobs/one.

    This job entry should be present in the database.
    """

    response = client.get("/api/v1/cluster/jobs/one?job_id=1000922", headers=valid_rest_auth_headers)
    assert response.content_type == 'application/json'
    D_job = response.json()

    assert "eligible_time" in D_job
    assert D_job["eligible_time"] == "1625666561"


def test_single_job_missing_1111111(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/cluster/jobs/one.

    This job entry should be missing from the database.
    """
    response = client.get("/api/v1/cluster/jobs/one?job_id=1111111", headers=valid_rest_auth_headers)
    assert response.content_type == 'application/json'
    D_job = response.json()
    assert D_job is None


@pytest.mark.parametrize("username", ("mario", "luigi", "toad", "peach"))
def test_api_list_four_valid_usernames(client, valid_rest_auth_headers, username):
    """
    Make a request to the REST API endpoint /api/v1/cluster/jobs/list.
    """

    response = client.get(f"/api/v1/cluster/jobs/list?user={username}", headers=valid_rest_auth_headers)
    assert response.content_type == 'application/json'
    LD_jobs = response.get_json()

    # make sure that every job returned has that username somewhere
    for D_job in LD_jobs:
        assert username in [
            D_job.get("mila_cluster_username", None), D_job.get("mila_user_account",   None),
            D_job.get("mila_email_username",   None), D_job.get("cc_account_username", None)]


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_api_list_two_invalid_usernames(client, valid_rest_auth_headers, username):
    """
    Make a request to the REST API endpoint /api/v1/cluster/jobs/list.
    """
    response = client.get(f"/api/v1/cluster/jobs/list?user={username}", headers=valid_rest_auth_headers)
    assert response.content_type == 'application/json'
    LD_jobs = response.get_json()

    # we expect no matches for those made-up names
    assert len(LD_jobs) == 0


# TODO : This job probably needs to fixing in order to be properly written.

def test_api_list_invalid_time(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/cluster/jobs/list.
    """
    response = client.get(f"/api/v1/cluster/jobs/list?time=this_is_not_a_valid_time", headers=valid_rest_auth_headers)
    assert response.content_type == 'application/json'
    LD_jobs = response.get_json()
    
    assert b"Field 'time' cannot be cast as a valid integer" in response.data
    assert b"this_is_not_a_valid_time" in response.data