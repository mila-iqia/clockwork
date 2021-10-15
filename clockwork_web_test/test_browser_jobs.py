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


def test_single_job_1000922(client):
    """
    Obviously, we need to compare the hardcoded fields with the values
    found in "fake_data.json" if we want to compare the results that
    we get when requesting "/jobs/single_job/<job_id>".
    """

    response = client.get("/jobs/one?job_id=1000922")
    assert "text/html" in response.content_type
    assert b"eligible_time" in response.data
    assert b"1625666561" in response.data


def test_single_job_missing_1111111(client):
    """
    This job entry should be missing from the database.
    """
    response = client.get("/jobs/one?job_id=1111111")
    assert "text/html" in response.content_type
    assert b"Found no job with job_id 1111111" in response.data


@pytest.mark.parametrize("username", ("mario", "luigi", "toad", "peach"))
def test_list_four_valid_usernames(client, username):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?user={username}")
    assert "text/html" in response.content_type
    assert username.encode("utf-8") in response.data


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_list_two_invalid_usernames(client, username):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?user={username}")
    response.status_code == 400
    print(response.data)
    # assert 'text/html' in response.content_type
    assert username.encode("utf-8") not in response.data  # notice the NOT


def test_list_invalid_time(client):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?time=this_is_not_a_valid_time")
    assert "text/html" in response.content_type

    assert (
        b"cannot be cast as a valid integer: this_is_not_a_valid_time" in response.data
    )
