"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import time
from pprint import pprint
import random
import json
import pytest


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

    original_D_job = random.choice(
        [
            D_job
            for D_job in fake_data["jobs"]
            if D_job["slurm"]["cluster_name"] == cluster_name
        ]
    )

    response = client.get(
        f"/api/v1/clusters/jobs/one?job_id={original_D_job['slurm']['job_id']}",
        headers=valid_rest_auth_headers,
    )
    assert "application/json" in response.content_type
    D_job = response.json

    for k1 in original_D_job:
        if k1 not in D_job:
            print(f"Missing key {k1} from fetched D_job.")
            pprint(original_D_job)
            pprint(D_job)
        else:
            for k2 in original_D_job[k1]:
                if k2 not in D_job:
                    print(f"Missing key {k2} from fetched D_job[{k1}].")
                    pprint(original_D_job)
                    pprint(D_job)
                else:
                    assert D_job[k1][k2] == original_D_job[k1][k2], (k1, k2)


def test_single_job_missing(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/one.

    This job entry should be missing from the database.
    """

    # Make sure you pick a random job_id that's not in the database.
    S_job_ids = set([D_job["slurm"]["job_id"] for D_job in fake_data["jobs"]])
    while True:
        job_id = "absent_job_%d" % int(random.random() * 1e7)
        if job_id not in S_job_ids:
            break

    response = client.get(
        f"/api/v1/clusters/jobs/one?job_id={job_id}", headers=valid_rest_auth_headers
    )
    assert "application/json" in response.content_type
    D_job = response.json  # no `json()` here, just `json`
    assert D_job == {}


def test_list_jobs_for_a_given_random_user(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.

    Note that the users for whom we list the jobs is probably not
    going to be the user encoded in the auth_headers, which we get
    from the environment variables "clockwork_tools_test_EMAIL"
    and "clockwork_tools_test_CLOCKWORK_API_KEY".

    We pick a user at random from our fake_data, and we see if we
    can list the jobs for that user.
    """

    def get_ground_truth(username, LD_jobs):
        return [
            D_job
            for D_job in LD_jobs
            if username
            in [
                D_job["cw"].get("mila_cluster_username", None),
                D_job["cw"].get("mila_email_username", None),
                D_job["cw"].get("cc_account_username", None),
            ]
        ]

    # Select something at random from the database, already populated
    # by the fake_data, in order to construct a good request.

    # let's avoid using a `while True` structure in a test
    for attempts in range(10):
        D_user = random.choice(fake_data["users"])
        assert D_user["accounts_on_clusters"]
        D_cluster_account = random.choice(list(D_user["accounts_on_clusters"].values()))
        username = D_cluster_account["username"]
        LD_jobs_ground_truth = get_ground_truth(username, fake_data["jobs"])
        # pick something that's interesting, and not something that should
        # return empty results, because then this test becomes vacuous
        if LD_jobs_ground_truth:
            break
    assert (
        LD_jobs_ground_truth
    ), "Failed to get an interesting test candidate for test_api_list_jobs_for_a_given_random_user. We hit the safety valve."

    response = client.get(
        f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers
    )
    assert response.content_type == "application/json"
    LD_jobs = response.get_json()

    # make sure that every job returned has that username somewhere
    for D_job in LD_jobs:
        assert username in [
            D_job["cw"].get("mila_cluster_username", None),
            D_job["cw"].get("mila_email_username", None),
            D_job["cw"].get("cc_account_username", None),
        ]

    # Let's just make sure that the set of job_id match for both the returned
    # results and the ground truth.
    # We could do an in-depth comparison with all the fields, but that seems
    # a bit zealous for now.
    assert set(D_job["slurm"]["job_id"] for D_job in LD_jobs) == set(
        D_job["slurm"]["job_id"] for D_job in LD_jobs_ground_truth
    )


def test_api_list_invalid_username(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
    """

    username = "some_username_absent_from_the_data"

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

    Make sure that the job entries returned are those that either than a `None`
    "end_time" field, or those that have a value that's more recent than the
    specified value.

    Since we have access to the `fake_data` we can make sure that all the
    corresponding entries are indeed returned. We can also use that to pick
    a query value that's sure to return something, because the `fake_data`
    contains jobs that are static and not very recent (i.e. asking for "everything
    that ended earlier than an hour ago" would return nothing except jobs
    that have "end_time" as `None`).
    """

    L_end_times = list(
        sorted(
            [
                D_job["slurm"]["end_time"]
                for D_job in fake_data["jobs"]
                if D_job["slurm"]["end_time"] is not None
            ]
        )
    )
    N = len(L_end_times)
    assert 10 <= N
    # Adding a +1 second because we don't want to balance on the edge
    # of whether $gt is inclusive or not in mongodb.
    # This isn't the point, so we add a +1.
    mid_end_time = L_end_times[N // 2] + 1

    # now let's find the ground truth
    LD_jobs_ground_truth = [
        D_job
        for D_job in fake_data["jobs"]
        if (D_job["slurm"]["end_time"] is None)
        or (mid_end_time <= D_job["slurm"]["end_time"])
    ]

    relative_mid_end_time = time.time() - mid_end_time
    assert 0 < relative_mid_end_time

    response = client.get(
        f"/api/v1/clusters/jobs/list?relative_time={relative_mid_end_time}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    LD_jobs_results = response.get_json()

    # Compare with ground truth. Let's just compare the "job_id"
    # of the jobs returned in both situations.
    assert set([D_job["slurm"]["job_id"] for D_job in LD_jobs_ground_truth]) == set(
        [D_job["slurm"]["job_id"] for D_job in LD_jobs_results]
    )
