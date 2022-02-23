import pytest
import random
from test_common.jobs_test_helpers import (
    helper_list_relative_time,
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
    LD_jobs = mtclient.jobs_list(cluster_name=cluster_name)
    validator(LD_jobs)


@pytest.mark.parametrize("username", ("yoshi", "koopatroopa"))
def test_api_list_invalid_username(mtclient, username):
    """ """
    LD_jobs = mtclient.jobs_list(user=username)
    # we expect no matches for those made-up names
    assert len(LD_jobs) == 0


@pytest.mark.parametrize("cluster_name", ("mila", "beluga", "cedar", "graham"))
def test_single_job_at_random(mtclient, fake_data, cluster_name):
    """
    This job entry should be present in the database.
    """
    validator, job_id = helper_single_job_at_random(fake_data, cluster_name)
    D_job = mtclient.jobs_one(job_id=job_id)
    validator(D_job)


def test_single_job_missing(mtclient, fake_data):
    """
    This job entry should be missing from the database.
    """
    validator, job_id = helper_single_job_missing(fake_data)
    D_job = mtclient.jobs_one(job_id=job_id)
    validator(D_job)


def test_list_relative_time(mtclient, fake_data):
    """
    Get jobs that are fresher than the time given.
    """

    validator, relative_mid_end_time = helper_list_relative_time(fake_data)
    LD_jobs = mtclient.jobs_list(relative_time=relative_mid_end_time)
    validator(LD_jobs)


def test_list_jobs_for_a_given_random_user(mtclient, fake_data):
    """
    Verify that we list the jobs properly for a given random user.
    """
    validator, username = helper_list_jobs_for_a_given_random_user(fake_data)
    LD_jobs = mtclient.jobs_list(user=username)
    validator(LD_jobs)


def test_jobs_user_dict_update(mtclient_student01):
    """
    Verify that we can modify that particular job for that user.
    We omit the `fake_data` test fixture because we hardcode
    certain details by hand.
    """

    # set two fields and make sure they are read back properly
    expected = {"pet_name": "fido", "nbr_cats": 10}
    #
    updated_user_dict = mtclient_student01.jobs_user_dict_update(
        job_id="284357",
        cluster_name="graham",
        update_pairs={"pet_name": "fido", "nbr_cats": 10},
    )
    assert updated_user_dict == expected
    #
    D_job = mtclient_student01.jobs_one(job_id="284357", cluster_name="graham")
    assert D_job["user"] == expected

    # update one field and add a new one, then make sure all three are as expected
    expected = {"pet_name": "garfield", "nbr_cats": 10, "nbr_dinosaurs": 42}
    #
    updated_user_dict = mtclient_student01.jobs_user_dict_update(
        job_id="284357",
        cluster_name="graham",
        update_pairs={"pet_name": "garfield", "nbr_dinosaurs": 42},
    )
    assert updated_user_dict == expected
    #
    D_job = mtclient_student01.jobs_one(job_id="284357", cluster_name="graham")
    assert D_job["user"] == expected
