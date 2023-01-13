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
from clockwork_web.core.pagination_helper import get_pagination_values
from clockwork_web.core.users_helper import (
    get_default_setting_value,
    get_available_clusters_from_db,
)


def test_redirect_index(client):
    response = client.get("/jobs/")
    assert response.status_code == 302
    assert response.headers["Location"] == "interactive"


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
    body_text = response.get_data(as_text=True)
    assert "start_time" in body_text
    assert D_job["slurm"]["name"] in body_text


def test_single_job_missing_423908482367(client):
    """
    This job entry should be missing from the database.
    """

    job_id = "423908482367"

    response = client.get("/jobs/one?job_id={}".format(job_id))
    assert "text/html" in response.content_type
    assert "Found no job with job_id" in response.get_data(as_text=True)


def test_single_job_no_id(client):
    response = client.get("/jobs/one")
    assert response.status_code == 400


def test_list_jobs_for_a_given_random_user(client, fake_data):
    """
    Make a request to /jobs/list.

    Not that we are not testing the actual contents on the web page.
    When we have the html contents better nailed down, we should
    add some tests to make sure we are returning good values there.
    """

    # the usual validator doesn't work on the html contents
    _, username = helper_list_jobs_for_a_given_random_user(fake_data)

    response = client.get(f"/jobs/list?username={username}")

    assert "text/html" in response.content_type

    assert username in response.get_data(as_text=True)
    # assert username.encode("utf-8") in response.data


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_list_jobs_invalid_username(client, username):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?username={username}")
    assert "text/html" in response.content_type
    assert username not in response.get_data(as_text=True)  # notice the NOT


def test_list_time(client, fake_data):
    _, relative_mid_end_time = helper_list_relative_time(fake_data)
    response = client.get(f"/jobs/list?relative_time={relative_mid_end_time}")
    assert response.status_code == 200
    assert "text/html" in response.content_type

    body_text = response.get_data(as_text=True)
    # assert "RUNNING" in body_text # Now that the jobs are sorted, and as we are expecting 25 jobs to be displayed by default, there is no more RUNNING jobs on this list for the current fake data
    assert "PENDING" in body_text


def test_list_invalid_time(client):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?relative_time=this_is_not_a_valid_relative_time")
    assert response.status_code == 400

    assert "cannot be cast as a valid integer:" in response.get_data(as_text=True)


def test_jobs(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the jobs are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
    )

    response = client.get("/jobs/list")
    body_text = response.get_data(as_text=True)
    for i in range(0, get_default_setting_value("nbr_items_per_page")):
        D_job = sorted_all_jobs[i]
        assert D_job["slurm"]["job_id"] in body_text


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_jobs_with_both_pagination_options(
    client, fake_data: dict[list[dict]], page_num, nbr_items_per_page
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated when using both pagination options: page_num and nbr_items_per_page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        page_num            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
    )

    # Get the response
    response = client.get(
        f"/jobs/list?page_num={page_num}&nbr_items_per_page={nbr_items_per_page}"
    )

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)
    # Assert that the retrieved jobs correspond to the expected jobs
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_jobs):
            D_job = sorted_all_jobs[i]
            assert D_job["slurm"]["job_id"] in body_text


@pytest.mark.parametrize("page_num", [1, 2, 3, "lala", 7.8, False])
def test_jobs_with_page_num_pagination_option(
    client, fake_data: dict[list[dict]], page_num
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated using only the page_num pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        page_num            The number of the page displaying the jobs
    """
    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
    )

    # Get the response
    response = client.get(f"/jobs/list?page_num={page_num}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, None
    )
    # Assert that the retrieved jobs correspond to the expected jobs

    body_text = response.get_data(as_text=True)
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_jobs):
            D_job = sorted_all_jobs[i]
            assert D_job["slurm"]["job_id"] in body_text


@pytest.mark.parametrize("nbr_items_per_page", [1, 29, 50, -1, [1, 2], True])
def test_jobs_with_page_num_pagination_option(
    client, fake_data: dict[list[dict]], nbr_items_per_page
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated using only the page_num pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
    )

    # Get the response
    response = client.get(f"/jobs/list?nbr_items_per_page={nbr_items_per_page}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, None, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)
    # Assert that the retrieved jobs correspond to the expected jobs
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_jobs):
            D_job = sorted_all_jobs[i]
            assert D_job["slurm"]["job_id"] in body_text


# No equivalent of "test_jobs_list_with_filter" here.


###
#   Tests for route_search
###
@pytest.mark.parametrize(
    "current_user_id,username,cluster_names,states,page_num,nbr_items_per_page",
    [
        (
            "student00@mila.quebec",
            "student05@mila.quebec",
            ["mila", "graham"],
            ["RUNNING", "PENDING"],
            2,
            2,
        ),
        (
            "student01@mila.quebec",
            "student10@mila.quebec",
            ["graham"],
            ["RUNNING", "PENDING"],
            2,
            2,
        ),
        (
            "student02@mila.quebec",
            "student13@mila.quebec",
            [],
            ["RUNNING", "PENDING"],
            1,
            40,
        ),
        ("student03@mila.quebec", "student13@mila.quebec", [], [], -1, -10),
        ("student04@mila.quebec", "student13@mila.quebec", [], [], -1, -10),
        ("student05@mila.quebec", "student03@mila.quebec", ["cedar"], [], 1, 50),
        ("student00@mila.quebec", None, ["cedar"], [], 2, 10),
        (
            "student06@mila.quebec",
            "student00@mila.quebec",
            ["mila", "cedar"],
            [],
            1,
            10,
        ),  # Nota bene: student06 has only access to the Mila cluster and student00 has jobs on Mila cluster and DRAC clusters
    ],
)
def test_route_search(
    client,
    fake_data,
    current_user_id,
    username,
    cluster_names,
    states,
    page_num,
    nbr_items_per_page,
):
    """
    Test the function route_search with different sets of arguments.

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        current_user_id     ID of the user requesting the jobs
        username            The user whose jobs we are looking for
        cluster_names      An array of the clusters on which we search jobs
        states              An array of the potential states of the jobs we want
                            to retrieve
        page_num            The number of the plage to display the jobs
        nbr_items_per_page  The number of jobs to display per page
    """
    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    ###
    # Look for the jobs we are expecting
    ###

    # Initialize the jobs we are expecting (before pagination)
    LD_prefiltered_jobs = []

    # Determine which filters we have to ignored
    ignore_username_filter = username is None
    ignore_states_filter = len(states) < 1

    # Define the union between the requested clusters and the clusters available
    # for the current user
    if len(cluster_names) < 1:
        requested_clusters = get_available_clusters_from_db(current_user_id)
    else:
        requested_clusters = [
            cluster_name
            for cluster_name in cluster_names
            if cluster_name in get_available_clusters_from_db(current_user_id)
        ]

    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
    )

    # For each job, determine if it could be expected (before applying the pagination)
    for D_job in sorted_all_jobs:
        # Retrieve the values we may want to test
        retrieved_username = D_job["cw"]["mila_email_username"]
        retrieved_cluster_name = D_job["slurm"]["cluster_name"]
        retrieved_state = D_job["slurm"]["job_state"]

        # Define the tests which will determine if the job is taken into account or not
        test_username = (retrieved_username == username) or ignore_username_filter
        test_cluster_names = retrieved_cluster_name in requested_clusters
        test_states = (retrieved_state in states) or ignore_states_filter

        # Select the jobs in regard of the predefined tests
        if test_username and test_cluster_names and test_states:
            LD_prefiltered_jobs.append(D_job)

    ###
    # Format the request
    ###

    # Initialize the call
    request_line = "/jobs/search?"

    # - username
    if username is not None:
        request_line += "username={}&".format(username)

    # - cluster_name
    if len(cluster_names) > 0:
        request_line += "cluster_name={}&".format(",".join(cluster_names))
    # - state
    if len(states) > 0:
        request_line += "state={}&".format(",".join(states))
    # - page_num
    if page_num:
        request_line += "page_num={}&".format(page_num)
    # - nbr_items_per_page
    if nbr_items_per_page:
        request_line += "nbr_items_per_page={}".format(nbr_items_per_page)

    # Retrieve the results
    response = client.get(request_line)

    ###
    # Apply the pagination
    ###

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)
    # Assert that the retrieved jobs correspond to the expected jobs
    for i in range(
        number_of_skipped_items, number_of_skipped_items + nbr_items_per_page
    ):
        if i < len(LD_prefiltered_jobs):
            D_job = LD_prefiltered_jobs[i]
            assert D_job["slurm"]["job_id"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_cc_portal(client, fake_data):
    """
    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us.
        fake_data           The data our tests are based on. It's a fixture.
    """
    # Choose a user who have access to all the clusters
    user_dict = fake_data["users"][0]
    assert user_dict["mila_cluster_username"] is not None
    assert user_dict["cc_account_username"] is not None

    # Log in to Clockwork as this user
    login_response = client.get(
        f"/login/testing?user_id={user_dict['mila_email_username']}"
    )
    assert login_response.status_code == 302  # Redirect

    # Hidden assumption that the /jobs/search will indeed give us
    # all the contents of the database if we set `nbr_items_per_page=10000`.
    # Note that asking for `want_json=True` wouldn't work here because
    # the url generated are only in the html rendering and not part of the original
    # database entries.
    request_line = "/jobs/search?cluster_name=beluga,narval&nbr_items_per_page=10000"
    # Retrieve the results
    response = client.get(request_line)

    body_text = response.get_data(as_text=True)

    i = 0
    for D_job in fake_data["jobs"]:
        D_job_slurm = D_job["slurm"]

        # just pick the first 50 or something
        if 50 <= i:
            break
        # don't try that with other clusters than beluga or narval because CC doesn't support it
        if D_job_slurm["cluster_name"] not in ["beluga", "narval"]:
            continue
        else:
            i += 1

        # Now comes the time to verify if the url for the CC portal was included in the html content.

        # https://portail.narval.calculquebec.ca/secure/jobstats/<username>/<jobid>
        # https://portail.beluga.calculquebec.ca/secure/jobstats/<username>/<jobid>
        url = f'https://portail.{D_job_slurm["cluster_name"]}.calculquebec.ca/secure/jobstats/{D_job_slurm["username"]}/{D_job_slurm["job_id"]}'
        assert url in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
