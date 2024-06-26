"""
Tests fort the clockwork_web.core.jobs_helper functions.
"""

import pytest

from clockwork_web.core.jobs_helper import *
from clockwork_web.db import get_db
from clockwork_web.core.pagination_helper import get_pagination_values
from clockwork_web.config import get_config


def test_get_jobs_with_user_props(app, client, fake_data):
    """Test that function get_jobs returns jobs with associated user props for test user email."""
    email = get_config("clockwork.test.email")

    # Map user props for test email with key (job_id, cluster_name)
    job_key_to_user_props = {
        (data["job_id"], data["cluster_name"]): data["props"]
        for data in fake_data["job_user_props"]
        if data["mila_email_username"] == email
    }
    assert job_key_to_user_props

    # Log in to Clockwork as test email
    login_response = client.get(f"/login/testing?user_id={email}")
    assert login_response.status_code == 302  # Redirect

    # Check user props
    with app.app_context():
        jobs, _ = get_jobs()
        nb_jobs_with_props = 0
        for job in jobs:
            job_key = (job["slurm"]["job_id"], job["slurm"]["cluster_name"])
            if job_key in job_key_to_user_props:
                assert "job_user_props" in job
                assert job["job_user_props"] == job_key_to_user_props[job_key]
                nb_jobs_with_props += 1
            else:
                assert "job_user_props" not in job
        assert nb_jobs_with_props == len(job_key_to_user_props)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_get_jobs_with_pagination(app, fake_data, page_num, nbr_items_per_page):
    """
    Test the function get_jobs by providing only pagination parameters.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, jobs_count) = get_jobs(
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
        )

        # Withdraw the "_id" element of the retrieved jobs
        LD_retrieved_jobs = [
            strip_artificial_fields_from_job(D_job) for D_job in LD_retrieved_jobs
        ]

        # Sort the jobs contained in the fake data by submit time, then job id
        sorted_all_jobs = sorted(
            fake_data["jobs"],
            key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )  # This is the default sorting

        # Assert that they correspond to the jobs we expect
        assert (
            LD_retrieved_jobs
            == sorted_all_jobs[
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )
        assert jobs_count == None


@pytest.mark.parametrize("want_count", [(True, False)])
def test_get_and_count_jobs_without_filters_or_pagination(app, fake_data, want_count):
    """
    Test the function get_jobs when want_count is True/False and all the jobs are requested.

    Parameters:
        app         The scope of our tests, used to set the context (to access MongoDB)
        fake_data   The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(want_count=want_count)

        # Withdraw the "_id" element of the retrieved jobs
        LD_retrieved_jobs = [
            strip_artificial_fields_from_job(D_job) for D_job in LD_retrieved_jobs
        ]

        # Now that we've removed the automatic sorting for REST,
        # we need to sort them ourselves if we want them sorted.
        LD_retrieved_jobs = list(
            sorted(
                LD_retrieved_jobs,
                key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
            )  # This is the default sorting
        )

        # Sort the jobs contained in the fake data by submit time, then by job id
        LD_truth_jobs = list(
            sorted(
                fake_data["jobs"],
                key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
            )  # This is the default sorting
        )

        if want_count:
            # Assert that the number nbr_total_jobs correspond to the filters without pagination
            # Here, we do not use filter nor pagination. Thus, this number should be the number of jobs.
            assert nbr_total_jobs == len(LD_truth_jobs)
        else:
            assert nbr_total_jobs == None

        # Assert that they correspond to the jobs we expect
        assert LD_retrieved_jobs == LD_truth_jobs


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_get_and_count_jobs_with_pagination(
    app, fake_data, page_num, nbr_items_per_page
):
    """
    Test the function get_jobs when want_count is True, and when providing only pagination parameters.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
            want_count=True,
        )

        # Withdraw the "_id" element of the retrieved jobs
        LD_retrieved_jobs = [
            strip_artificial_fields_from_job(D_job) for D_job in LD_retrieved_jobs
        ]

        # Sort the jobs contained in the fake data by submit time, then by job id
        sorted_all_jobs = sorted(
            fake_data["jobs"],
            key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )  # This is the default sorting

        # Assert that they correspond to the jobs we expect
        assert (
            LD_retrieved_jobs
            == sorted_all_jobs[
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )

        # Assert that the retrieved number correspond to the expected number of jobs
        # Here, we only apply pagination and not filters, so that the expected number
        # is the total of jobs in the database
        assert nbr_total_jobs == len(sorted_all_jobs)


@pytest.mark.parametrize("page_num, nbr_items_per_page", [(1, 10), (3, 2)])
def test_get_and_count_jobs_by_mail_with_pagination(
    app, fake_data, page_num, nbr_items_per_page
):
    """
    Test the function get_jobs when looking for the jobs of a specific user and when want_count is True.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Choose the query conditions applied in this test
        mila_email_username = "student02@mila.quebec"

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(
            username=mila_email_username,
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
            want_count=True,
        )

        # Withdraw the "_id" element of the retrieved jobs
        LD_retrieved_jobs = [
            strip_artificial_fields_from_job(D_job) for D_job in LD_retrieved_jobs
        ]

        # Sort the jobs contained in the fake data by submit time, then by job id
        sorted_all_jobs = sorted(
            fake_data["jobs"],
            key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )  # This is the default sorting

        # Retrieve the expected jobs
        LD_expected_jobs = []
        for D_job in sorted_all_jobs:
            if D_job["cw"]["mila_email_username"] == mila_email_username:
                LD_expected_jobs.append(D_job)

        # Assert that they correspond to the jobs we expect
        assert (
            LD_retrieved_jobs
            == LD_expected_jobs[
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )

        # Assert that the retrieved number correspond to the number of expected jobs
        # before applying the pagination
        assert nbr_total_jobs == len(LD_expected_jobs)


@pytest.mark.parametrize("page_num, nbr_items_per_page", [(1, 10), (3, 2)])
def test_get_and_count_jobs_by_cluster_and_job_state_with_pagination(
    app, fake_data, page_num, nbr_items_per_page
):
    """
    Test the function get_jobs when looking for the jobs of a specific user and when want_count is True.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the jobs
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Set up the filter applied in this test
        L_clusters = ["mila", "graham"]
        L_job_states = ["RUNNING"]

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(
            cluster_names=L_clusters,
            job_states=L_job_states,
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
            want_count=True,
        )

        # Withdraw the "_id" element of the retrieved jobs
        LD_retrieved_jobs = [
            strip_artificial_fields_from_job(D_job) for D_job in LD_retrieved_jobs
        ]

        # Sort the jobs contained in the fake data by submit time, then by job id
        sorted_all_jobs = sorted(
            fake_data["jobs"],
            key=lambda d: (-d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )  # This is the default sorting

        # Retrieve the expected jobs
        LD_expected_jobs = []
        for D_job in sorted_all_jobs:
            if (D_job["slurm"]["cluster_name"] in L_clusters) and (
                D_job["slurm"]["job_state"] in L_job_states
            ):
                LD_expected_jobs.append(D_job)

        # Assert that they correspond to the jobs we expect
        assert (
            LD_retrieved_jobs
            == LD_expected_jobs[
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )

        # Assert that the retrieved number correspond to the number of expected jobs
        # before [{"cw.mila_email_username": "student03@mila.quebec"}]applying the pagination
        assert nbr_total_jobs == len(LD_expected_jobs)


@pytest.mark.parametrize(
    "given_filters, expected_filter",
    [
        ([], {}),
        (
            [{"cw.mila_email_username": "student03@mila.quebec"}],
            {"cw.mila_email_username": "student03@mila.quebec"},
        ),
        (
            [{"$in": ["graham", "mila"]}, {"$in": ["RUNNING"]}],
            {"$and": [{"$in": ["graham", "mila"]}, {"$in": ["RUNNING"]}]},
        ),
    ],
)
def test_combine_all_mongodb_filters(given_filters, expected_filter):
    """
    Test the function combine_all_mongodb_filters.

    Parameters:
        given_filters       Filters given as arguments of combine_all_mongodb_filters to test the
                            function.
        expected_filter     Filter expected in return of the function.
    """
    # Call combine_all_mongodb_filters with the given input
    returned_filter = combine_all_mongodb_filters(*given_filters)

    # Compare the output with the expected result
    assert returned_filter == expected_filter


@pytest.mark.parametrize(
    "username,job_ids,cluster_names,job_states,expected_result",
    [
        (None, [], None, [], {}),  # If nothing has been provided, the filter is empty
        (
            "student00@mila.quebec",
            [123, 456],
            ["mila", "narval"],
            ["PENDING", "RUNNING"],
            {
                "$and": [
                    {"cw.mila_email_username": "student00@mila.quebec"},
                    {"slurm.job_id": {"$in": [123, 456]}},
                    {"slurm.cluster_name": {"$in": ["mila", "narval"]}},
                    {"slurm.job_state": {"$in": ["PENDING", "RUNNING"]}},
                ]
            },
        ),
    ],
)
def test_get_global_filter(
    username, job_ids, cluster_names, job_states, expected_result
):
    """
    Test the function get_global_filter.

    Parameters:
        username        ID of the user of whose jobs we want to retrieve
        job_ids         List of the IDs of the jobs we are looking for
        cluster_names   List of names of the clusters on which the expected jobs run/will run or have run
        job_states      List of names of job states the expected jobs could have
        expected_result Result we are expecting as output of the get_global_filter function when
                        providing the associated parameters
    """
    assert (
        get_global_filter(
            username=username,
            job_ids=job_ids,
            cluster_names=cluster_names,
            job_states=job_states,
        )
        == expected_result
    )
