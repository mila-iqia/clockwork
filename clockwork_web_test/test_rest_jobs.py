
"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

from pprint import pprint
import random
import json
import pytest


def test_single_job_at_random(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/one.

    This job entry should be present in the database.
    """

    original_D_job = random.choice(fake_data['jobs'])

    response = client.get(f"/api/v1/clusters/jobs/one?job_id={original_D_job['job_id']}", headers=valid_rest_auth_headers)
    assert 'application/json' in response.content_type
    D_job = response.json

    for k in original_D_job:
        # That "grafana_helpers" is just pollution in the original data,
        # and we're stripping it automatically in clockwork_web, so this
        # is why we won't see it here.
        if k in ["grafana_helpers", "best_guess_for_username"]:
            continue

        if k not in D_job:
            print(f"Missing key {k} from fetched D_job.")
            pprint(original_D_job)
            pprint(D_job)

        assert D_job[k] == original_D_job[k], k



def test_single_job_missing(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/one.

    This job entry should be missing from the database.
    """

    # Make sure you pick a random job_id that's not in the database.
    S_job_ids = set([D_job['job_id'] for D_job in fake_data['jobs']])
    while True:
        job_id = int(random.random()*1e7)
        if job_id not in S_job_ids:
            break

    response = client.get(f"/api/v1/clusters/jobs/one?job_id={job_id}", headers=valid_rest_auth_headers)
    assert 'application/json' in response.content_type
    D_job = response.json  # no `json()` here, just `json`
    assert D_job == {}


# @pytest.mark.parametrize("username", ("mario", "luigi", "toad", "peach"))
# def test_api_list_four_valid_usernames(client, valid_rest_auth_headers, username):
#     """
#     Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
#     """

#     response = client.get(f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers)
#     assert response.content_type == 'application/json'
#     LD_jobs = response.get_json()

#     # make sure that every job returned has that username somewhere
#     for D_job in LD_jobs:
#         assert username in [
#             D_job.get("mila_cluster_username", None), D_job.get("mila_user_account",   None),
#             D_job.get("mila_email_username",   None), D_job.get("cc_account_username", None)]


# @pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
# def test_api_list_two_invalid_usernames(client, valid_rest_auth_headers, username):
#     """
#     Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
#     """
#     response = client.get(f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers)
#     assert response.content_type == 'application/json'
#     LD_jobs = response.get_json()

#     # we expect no matches for those made-up names
#     assert len(LD_jobs) == 0


# # TODO : This job probably needs to fixing in order to be properly written.

# def test_api_list_invalid_time(client, valid_rest_auth_headers):
#     """
#     Make a request to the REST API endpoint /api/v1/clusters/jobs/list.
#     """
#     response = client.get(f"/api/v1/clusters/jobs/list?time=this_is_not_a_valid_time", headers=valid_rest_auth_headers)
#     assert response.content_type == 'application/json'
#     LD_jobs = response.get_json()
    
#     assert b"Field 'time' cannot be cast as a valid integer" in response.data
#     assert b"this_is_not_a_valid_time" in response.data