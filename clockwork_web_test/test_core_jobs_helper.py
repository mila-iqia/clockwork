"""
Tests fort the clockwork_web.core.jobs_helper functions.
"""

import pytest

from clockwork_web.core.jobs_helper import *
from clockwork_web.db import get_db
from clockwork_web.core.pagination_helper import get_pagination_values


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
            key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )

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
                key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
            )
        )

        # Sort the jobs contained in the fake data by submit time, then by job id
        LD_truth_jobs = list(
            sorted(
                fake_data["jobs"],
                key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
            )
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
            key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )

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

        # Set up the filter applied in this test
        mila_email_username = "student02@mila.quebec"
        filter = {"cw.mila_email_username": mila_email_username}

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(
            mongodb_filter=filter,
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
            key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )

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
def test_get_and_count_jobs_by_cluster_and_state_with_pagination(
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
        L_states = ["RUNNING"]
        filter = {
            "$and": [
                {"slurm.cluster_name": {"$in": L_clusters}},
                {"slurm.job_state": {"$in": L_states}},
            ]
        }

        # Retrieve the jobs we want to list
        (LD_retrieved_jobs, nbr_total_jobs) = get_jobs(
            mongodb_filter=filter,
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
            key=lambda d: (d["slurm"]["submit_time"], d["slurm"]["job_id"]),
        )

        # Retrieve the expected jobs
        LD_expected_jobs = []
        for D_job in sorted_all_jobs:
            if (D_job["slurm"]["cluster_name"] in L_clusters) and (
                D_job["slurm"]["job_state"] in L_states
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
