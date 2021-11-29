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

    def get_ground_truth(username, LD_jobs):
        return [D_job for D_job in LD_jobs if username in [
            D_job["cw"].get("mila_cluster_username", None),
            D_job["cw"].get("mila_email_username", None),
            D_job["cw"].get("cc_account_username", None)]]

    for retries in range(10):
        # Select something at random from the database.
        D_user = random.choice(fake_data["users"])
        assert D_user["accounts_on_clusters"]
        D_cluster_account = random.choice(list(D_user["accounts_on_clusters"].values()))
        username = D_cluster_account["username"]
        LD_jobs_ground_truth = get_ground_truth(username, fake_data["jobs"])
        # pick something that's interesting, and not something that should
        # return empty results, because then this test becomes vacuous
        if LD_jobs_ground_truth:
            break
    assert LD_jobs_ground_truth, "Failed to get an interesting test candidate for test_list_jobs_for_a_given_random_user. We hit the safety valve."


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
    response = client.get(f"/jobs/list?time=this_is_not_a_valid_time")
    assert "text/html" in response.content_type

    assert (
        b"cannot be cast as a valid integer: this_is_not_a_valid_time" in response.data
    )
