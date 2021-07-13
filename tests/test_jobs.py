
"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask

"""

import json
import pytest

def test_create(client, user, app):
    
    print(client)
    print(user)

    with app.app_context():
        assert 2 == 2


def test_single_job_1000922(client):
    """
    Obviously, we need to compare the hardcoded fields with the values
    found in "fake_data.json" if we want to compare the results that
    we get when requesting "/jobs/single_job/<job_id>".
    """

    response = client.get("/jobs/single_job/1000922")
    assert b"eligible_time" in response.data
    assert b"1625666561" in response.data


def test_single_job_missing_1111111(client):
    """
    This job entry should be missing from the database.
    """
    response = client.get("/jobs/single_job/1111111")
    assert b"Found no job with job_id 1111111" in response.data


@pytest.mark.parametrize("username", ("mario", "luigi", "toad", "peach"))
def test_api_list_four_valid_usernames(client, username):
    """
    Make a request to the REST API endpoint /jobs/api/list.
    """

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    data = {
        "query_filter": {'user': username}
    }
    url = "/jobs/api/list"
    response = client.post(url, data=json.dumps(data), headers=headers)
    
    assert response.content_type == mimetype
    LD_jobs = response.get_json()

    # make sure that every job returned has that username somewhere
    for D_job in LD_jobs:
        assert username in [
            D_job["mila_cluster_username"], D_job["mila_user_account"],
            D_job["mila_email_username"], D_job["cc_account_username"]]


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_api_list_two_invalid_usernames(client, username):
    """
    Make a request to the REST API endpoint /jobs/api/list.
    """
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    data = {
        "query_filter": {'user': username}
    }
    url = "/jobs/api/list"
    response = client.post(url, data=json.dumps(data), headers=headers)

    assert response.content_type == mimetype
    LD_jobs = response.get_json()
    # we expect no matches for those made-up names
    assert len(LD_jobs) == 0


def test_api_list_invalid_time(client):
    """
    Make a request to the REST API endpoint /jobs/api/list.
    """

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    data = {
        "query_filter": {'time': "this_is_not_a_valid_time"}
    }
    url = "/jobs/api/list"

    response = client.post(url, data=json.dumps(data), headers=headers)
    
    assert b"Field 'time' cannot be cast as a valid integer" in response.data
    assert b"this_is_not_a_valid_time" in response.data