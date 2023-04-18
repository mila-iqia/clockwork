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
import re
import pytest
from clockwork_web.core.jobs_helper import get_inferred_job_states

from test_common.jobs_test_helpers import (
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

##########
# Global #
##########


def test_redirect_index(client):
    response = client.get("/jobs/")
    assert response.status_code == 302
    assert response.headers["Location"] == "interactive"


####################
# Single job route #
####################


def test_single_job(client, fake_data):
    """
    Obviously, we need to compare the hardcoded fields with the values
    found in "fake_data.json" if we want to compare the results that
    we get when requesting "/jobs/one/<job_id>".
    """
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    D_job = random.choice(fake_data["jobs"])
    jod_id = D_job["slurm"]["job_id"]

    response = client.get(f"/jobs/one?job_id={jod_id}")

    assert "text/html" in response.content_type
    body_text = response.get_data(as_text=True)
    assert "start_time" in body_text
    assert D_job["slurm"]["name"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_job_missing_423908482367(client):
    """
    This job entry should be missing from the database.
    """
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    job_id = "423908482367"

    response = client.get("/jobs/one?job_id={}".format(job_id))
    assert "text/html" in response.content_type
    assert "Found no job with job_id" in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_job_no_id(client):
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    response = client.get("/jobs/one")
    assert response.status_code == 400

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


#######################
#   Jobs search route #
#######################


def test_search_jobs_for_a_given_random_user(client, fake_data):
    """
    Make a request to /jobs/search.

    Not that we are not testing the actual contents on the web page.
    When we have the html contents better nailed down, we should
    add some tests to make sure we are returning good values there.
    """
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # the usual validator doesn't work on the html contents
    _, username = helper_list_jobs_for_a_given_random_user(fake_data)

    response = client.get(f"/jobs/search?username={username}")

    assert "text/html" in response.content_type
    assert username in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_search_jobs_invalid_username(client, username):
    """
    Make a request to /jobs/search.
    """
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    response = client.get(f"/jobs/search?username={username}")
    assert "text/html" in response.content_type
    assert "/jobs/one" not in response.get_data(
        as_text=True
    )  # Check that no job is returned

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_jobs(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the jobs are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (
            d["slurm"]["submit_time"],
            -int(d["slurm"]["job_id"]),
        ),  # These are the default values for the sorting
        reverse=True,
    )

    response = client.get("/jobs/search")
    body_text = response.get_data(as_text=True)
    # only the first ones from the list
    for D_job in sorted_all_jobs[: get_default_setting_value("nbr_items_per_page")]:
        assert D_job["slurm"]["job_id"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


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
    # Define the user we want to use for this test
    current_user_id = "student00@mila.quebec"  # Can access all clusters

    # Log in to Clockwork
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (
            d["slurm"]["submit_time"],
            -int(d["slurm"]["job_id"]),
        ),  # These are the default values for the sorting
        reverse=True,
    )

    # Get the response
    response = client.get(
        f"/jobs/search?page_num={page_num}&nbr_items_per_page={nbr_items_per_page}"
    )

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, page_num, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)
    # Assert that the retrieved jobs correspond to the expected jobs
    for D_job in sorted_all_jobs[
        number_of_skipped_items : number_of_skipped_items + nbr_items_per_page
    ]:
        assert D_job["slurm"]["job_id"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


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
    # Define the user we want to use for this test
    current_user_id = "student00@mila.quebec"  # Can access all clusters

    # Log in to Clockwork
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (
            d["slurm"]["submit_time"],
            -int(d["slurm"]["job_id"]),
        ),  # These is the default sorting
        reverse=True,
    )

    # Get the response
    response = client.get(f"/jobs/search?page_num={page_num}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, page_num, None
    )
    # Assert that the retrieved jobs correspond to the expected jobs

    body_text = response.get_data(as_text=True)
    for D_job in sorted_all_jobs[
        number_of_skipped_items : (number_of_skipped_items + nbr_items_per_page)
    ]:
        assert D_job["slurm"]["job_id"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize("nbr_items_per_page", [1, 29, 50, -1, [1, 2], True])
def test_jobs_with_nbr_items_per_page_pagination_option(
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
    # Define the user we want to use for this test
    current_user_id = "student00@mila.quebec"  # Can access all clusters

    # Log in to Clockwork
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Sort the jobs contained in the fake data by submit time, then by job id
    sorted_all_jobs = sorted(
        fake_data["jobs"],
        key=lambda d: (
            d["slurm"]["submit_time"],
            -int(d["slurm"]["job_id"]),
        ),  # This is the default sorting option
        reverse=True,
    )

    # Get the response
    response = client.get(f"/jobs/search?nbr_items_per_page={nbr_items_per_page}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, None, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)
    # Assert that the retrieved jobs correspond to the expected jobs
    for D_job in sorted_all_jobs[
        number_of_skipped_items : (number_of_skipped_items + nbr_items_per_page)
    ]:
        assert D_job["slurm"]["job_id"] in body_text

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "current_user_id,username,cluster_names,job_states,page_num,nbr_items_per_page,sort_by,sort_asc",
    [
        (
            "student00@mila.quebec",
            "student05@mila.quebec",
            ["mila", "graham"],
            ["RUNNING", "PENDING"],
            2,
            2,
            "user",
            -1,
        ),
        (
            "student01@mila.quebec",
            "student10@mila.quebec",
            ["graham"],
            ["RUNNING", "PENDING"],
            2,
            2,
            "submit_time",
            1,
        ),
        (
            "student00@mila.quebec",
            "student00@mila.quebec",
            ["graham"],
            ["RUNNING", "PENDING"],
            2,
            10,
            "job_id",
            1,
        ),
        (
            "student02@mila.quebec",
            "student13@mila.quebec",
            [],
            ["RUNNING", "PENDING"],
            1,
            40,
            "name",
            -1,
        ),
        (
            "student03@mila.quebec",
            "student13@mila.quebec",
            [],
            [],
            -1,
            -10,
            "end_time",
            1,
        ),
        ("student04@mila.quebec", "student13@mila.quebec", [], [], -1, -10, "user", 1),
        (
            "student05@mila.quebec",
            "student03@mila.quebec",
            ["cedar"],
            [],
            1,
            50,
            "job_state",
            -1,
        ),
        ("student00@mila.quebec", None, ["cedar"], [], 2, 10, "name", 1),
        (
            "student06@mila.quebec",
            "student00@mila.quebec",
            ["mila", "cedar"],
            [],
            1,
            10,
            "end_time",
            -1,
        ),
        # Note: student06 has only access to the Mila cluster and student00 has jobs on Mila cluster and DRAC clusters,
        #       so these arguments test that student06 should NOT see the jobs on DRAC clusters
        (
            "student06@mila.quebec",
            "student00@mila.quebec",
            ["cedar"],
            [],
            1,
            10,
            "start_time",
            -1,
        ),
        # Note: student06 has only access to the Mila cluster and student00 has jobs on Mila cluster and DRAC clusters,
        #       so these arguments test that student06 should NOT see the jobs on DRAC clusters
    ],
)
def test_route_search(
    client,
    fake_data,
    current_user_id,
    username,
    cluster_names,
    job_states,
    page_num,
    nbr_items_per_page,
    sort_by,
    sort_asc,
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
        cluster_names       An array of the clusters on which we search jobs
        job_states          An array of the potential states of the jobs we want
                            to retrieve
        page_num            The number of the plage to display the jobs
        nbr_items_per_page  The number of jobs to display per page
        sort_by             String specifying the field on which we are based
                            to sort the jobs. Its value could be "cluster_name",
                            "user", "job_id", "name" (for job name), "job_state",
                            "submit_time", "start_time" and "end_time". Default is
                            "submit_time"
        sort_asc            Integer from {-1;1} specifying if the sorting is
                            ascending (1) or descending (-1). Default is 1.
    """
    # Log in to Clockwork as the current_user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    ###
    # We need to manually build what the correct answer should be
    # in order to test that we get the desired behavior.
    ###

    # Initialize the jobs we are expecting (before pagination)
    LD_prefiltered_jobs = []

    # Determine which filters we have to ignore
    ignore_username_filter = username is None
    job_states = get_inferred_job_states(job_states)
    ignore_job_states_filter = len(job_states) < 1

    # Intersection between the requested clusters (if specified)
    # and the clusters available for the current user.
    if not cluster_names:
        cluster_names = get_available_clusters_from_db(current_user_id)
    requested_clusters = set(cluster_names).intersection(
        set(get_available_clusters_from_db(current_user_id))
    )

    # Define the filters to sort the jobs
    if sort_by == "user":
        sorting_key = lambda d: (
            # d["cw"]["mila_email_username"] or "" returns "" if the value of d["cw"]["mila_email_username"] is None
            # This is done because None is not comparable to the strings
            d["cw"]["mila_email_username"] or "",
            sort_asc * int(d["slurm"]["job_id"]),
        )
    elif sort_by == "job_id":
        sorting_key = lambda d: (d["slurm"]["job_id"])
    elif sort_by in ["submit_time", "start_time", "end_time"]:
        sorting_key = lambda d: (
            # d["slurm"][sort_by] or 0 returns 0 if the value of d["slurm"][sort_by] is None
            # This is done because None is not comparable to timestamps
            d["slurm"][sort_by] or 0,  # time.time(),
            sort_asc * int(d["slurm"]["job_id"]),
        )
    else:
        sorting_key = lambda d: (
            # d["slurm"][sort_by] or "" returns "" if the value of d["slurm"][sort_by] is None
            # This is done because in order to make this default value comparable to the other
            # fields (which should be strings in this else condition)
            d["slurm"][sort_by] or "",
            sort_asc * int(d["slurm"]["job_id"]),
        )

    # Sort the jobs contained in the fake data by the sorting field, then by job id
    sorted_all_jobs = sorted(fake_data["jobs"], key=sorting_key, reverse=sort_asc == -1)

    # For each job, determine if it could be expected (before applying the pagination)
    for D_job in sorted_all_jobs:
        # Retrieve the values we may want to test
        retrieved_username = D_job["cw"]["mila_email_username"]
        retrieved_cluster_name = D_job["slurm"]["cluster_name"]
        retrieved_job_state = D_job["slurm"]["job_state"]

        # Define the tests which will determine if the job is taken into account or not
        test_username = (retrieved_username == username) or ignore_username_filter
        test_cluster_names = retrieved_cluster_name in requested_clusters
        test_job_states = (
            retrieved_job_state in job_states
        ) or ignore_job_states_filter

        # Select the jobs in regard of the predefined tests
        if test_username and test_cluster_names and test_job_states:
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
    if cluster_names:
        request_line += "cluster_name={}&".format(",".join(cluster_names))
    # - job_state
    if job_states:
        request_line += "aggregated_job_state={}&".format(",".join(job_states))
    # - page_num
    if page_num:
        request_line += "page_num={}&".format(page_num)
    # - nbr_items_per_page
    if nbr_items_per_page:
        request_line += "nbr_items_per_page={}&".format(nbr_items_per_page)
    # - sort_by
    if sort_by:
        request_line += "sort_by={}&".format(sort_by)
    # - sort_asc
    if sort_asc:
        request_line += "sort_asc={}".format(sort_asc)

    # Retrieve the results
    response = client.get(request_line)

    ###
    # Apply the pagination
    ###

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, page_num, nbr_items_per_page
    )

    body_text = response.get_data(as_text=True)

    # Assert that the retrieved jobs correspond to the expected jobs
    expected_jobs = LD_prefiltered_jobs[
        number_of_skipped_items : (number_of_skipped_items + nbr_items_per_page)
    ]
    expected_ids = [x["slurm"]["job_id"] for x in expected_jobs]
    found_ids = re.findall(pattern="job_id=([0-9]+)", string=body_text)

    if found_ids != expected_ids:

        def _find(job_id):
            for job in fake_data["jobs"]:
                if job["slurm"]["job_id"] == job_id:
                    pprint(job)
                    return

        for job_id in set(found_ids) - set(expected_ids):
            print("Found job that should NOT be there:")
            _find(job_id)
        for job_id in set(expected_ids) - set(found_ids):
            print("Did not find job that SHOULD be there:")
            _find(job_id)

    assert found_ids == expected_ids

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
