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

    response = client.get(f"/jobs/list?user={username}")

    assert "text/html" in response.content_type
    assert username.encode("utf-8") in response.data


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_list_jobs_invalid_username(client, username):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?user={username}")
    assert "text/html" in response.content_type
    assert username.encode("utf-8") not in response.data  # notice the NOT


def test_list_time(client, fake_data):
    _, relative_mid_end_time = helper_list_relative_time(fake_data)
    response = client.get(f"/jobs/list?relative_time={relative_mid_end_time}")
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"RUNNING" in response.data
    assert b"PENDING" in response.data


def test_list_invalid_time(client):
    """
    Make a request to /jobs/list.
    """
    response = client.get(f"/jobs/list?relative_time=this_is_not_a_valid_relative_time")
    assert response.status_code == 400

    assert (
        b"cannot be cast as a valid integer: this_is_not_a_valid_relative_time"
        in response.data
    )


def test_jobs(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the jobs are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    response = client.get("/jobs/list")
    for i in range(0, 40):  # TODO: centralize this value
        D_job = fake_data["jobs"][i]
        assert D_job["slurm"]["job_id"].encode("utf-8") in response.data


@pytest.mark.parametrize(
    "num_page,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_jobs_with_both_pagination_options(
    client, fake_data: dict[list[dict]], num_page, nbr_items_per_page
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated when using both pagination options: num_page and nbr_items_per_page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        num_page            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Get the response
    response = client.get("/jobs/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, num_page, nbr_items_per_page
    )

    # Assert that the retrieved jobs correspond to the expected jobs
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_job = fake_data["jobs"][i]
            assert D_job["slurm"]["job_id"].encode("utf-8") in response.data


@pytest.mark.parametrize("num_page", [1, 2, 3, "lala", 7.8, False])
def test_jobs_with_num_page_pagination_option(
    client, fake_data: dict[list[dict]], num_page
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated using only the num_page pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        num_page            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Get the response
    response = client.get("/jobs/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, num_page, None
    )
    # Assert that the retrieved jobs correspond to the expected jobs

    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_job = fake_data["jobs"][i]
            assert D_job["slurm"]["job_id"].encode("utf-8") in response.data


@pytest.mark.parametrize("nbr_items_per_page", [1, 29, 50, -1, [1, 2], True])
def test_jobs_with_num_page_pagination_option(
    client, fake_data: dict[list[dict]], nbr_items_per_page
):
    """
    Check that all the expected names of the jobs are present in the HTML
    generated using only the num_page pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Get the response
    response = client.get("/jobs/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected jobs
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, None, nbr_items_per_page
    )
    # Assert that the retrieved jobs correspond to the expected jobs

    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_job = fake_data["jobs"][i]
            assert D_job["slurm"]["job_id"].encode("utf-8") in response.data


# No equivalent of "test_jobs_list_with_filter" here.
