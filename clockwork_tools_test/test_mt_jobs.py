import pytest
import random
from test_common.jobs_test_helpers import (
    helper_single_job_missing,
    helper_single_job_at_random,
    helper_list_jobs_for_a_given_random_user,
    helper_jobs_list_with_filter,
)


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth")
)
def test_jobs_list_with_filter(mtclient, fake_data, cluster_name):
    """
    Test the `jobs_list` command. This is just to make sure that the filtering works
    and the `cluster_name` argument is functional.

    Note that "sephiroth" is not a valid cluster, so we will expect empty lists as results.
    """
    validator = helper_jobs_list_with_filter(fake_data, cluster_name=cluster_name)
    LD_jobs = mtclient.search_jobs(cluster_name=cluster_name)
    validator(LD_jobs)


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_api_list_invalid_username(mtclient, username):
    """ """
    LD_retrieved_jobs = mtclient.search_jobs(username=username)
    # we expect no matches for those made-up names
    assert len(LD_retrieved_jobs) == 0


@pytest.mark.parametrize("cluster_name", ("mila", "beluga", "cedar", "graham"))
def test_single_job_at_random(mtclient, fake_data, cluster_name):
    """
    This job entry should be present in the database.
    """
    validator, job_id = helper_single_job_at_random(fake_data, cluster_name)
    D_job = mtclient.search_jobs(job_id=job_id)
    validator(D_job)


def test_single_job_missing(mtclient, fake_data):
    """
    This job entry should be missing from the database.
    """
    validator, job_id = helper_single_job_missing(fake_data)
    D_job = mtclient.search_jobs(job_id=job_id)
    validator(D_job)


def test_list_jobs_for_a_given_random_user(mtclient, fake_data):
    """
    Verify that we list the jobs properly for a given random user.
    """
    validator, username = helper_list_jobs_for_a_given_random_user(fake_data)
    LD_jobs = mtclient.search_jobs(username=username)
    validator(LD_jobs)

