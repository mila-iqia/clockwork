"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import random
import json
import pytest
from test_common.jobs_test_helpers import (
    helper_list_relative_time,
    helper_single_job_missing,
    helper_single_job_at_random,
    helper_list_jobs_for_a_given_random_user,
    helper_jobs_list_with_filter,
)


def test_single_job(client, fake_data):
    """
    Obviously, we need to compare the hardcoded fields with the values
    found in "fake_data.json" if we want to compare the results that
    we get when requesting "/jobs/one/<job_id>".
    """

    D_job = random.choice(fake_data["jobs"])
    jod_id = D_job["slurm"]["job_id"]

    response = client.get(f"/jobs/one?job_id={jod_id}")

    assert "text/html" in response.content_type
    assert b"start_time" in response.data
    assert D_job["slurm"]["name"].encode("utf-8") in response.data


def test_single_job_missing_423908482367(client):
    """
    This job entry should be missing from the database.
    """

    job_id = "423908482367"

    response = client.get("/jobs/one?job_id=423908482367")
    assert "text/html" in response.content_type
    assert b"Found no job with job_id 423908482367" in response.data


def test_list_jobs_for_a_given_random_user(client, fake_data):
    """
    Make a request to /jobs/list.

    Not that we are not testing the actual contents on the web page.
    When we have the html contents better nailed down, we should
    add some tests to make sure we are returning good values there.
    """

    # the usual validator doesn't work on the html contents
    _, username = helper_list_jobs_for_a_given_random_user(fake_data)

    response = client.get(f"/jobs/list?user={username}")

    assert "text/html" in response.content_type
    assert username.encode("utf-8") in response.data


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_list_jobs_invalid_username(client, username):
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
    response = client.get(f"/jobs/list?relative_time=this_is_not_a_valid_relative_time")
    assert "text/html" in response.content_type

    assert (
        b"cannot be cast as a valid integer: this_is_not_a_valid_relative_time"
        in response.data
    )


# No equivalent of "test_jobs_list_with_filter" here.
