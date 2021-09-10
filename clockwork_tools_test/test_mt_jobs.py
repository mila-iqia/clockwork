
import pytest
import random

@pytest.mark.parametrize("cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth"))
def test_jobs_list_with_filter(mtclient, fake_data, cluster_name):
    """
    Test the `jobs_list` command. This is just to make sure that the filtering works
    and the `cluster_name` argument is functional.

    Note that "sephiroth" is not a valid cluster, so we will expect empty lists as results.
    """
    LD_jobs = mtclient.jobs_list(cluster_name=cluster_name)
    LD_original_jobs = [D_job for D_job in fake_data['jobs'] if D_job["cluster_name"] == cluster_name]

    assert len(LD_jobs) == len(LD_original_jobs), (
        "Lengths of lists don't match, so we shouldn't expect them to be able "
        "to match the elements themselves."
    )

    # agree on some ordering so you can zip the lists and have
    # matching elements in the same order
    LD_jobs = list(sorted(LD_jobs, key=lambda D_job: D_job['job_id']))
    LD_original_jobs = list(sorted(LD_original_jobs, key=lambda D_job: D_job['job_id']))

    # compare all the dicts one by one
    for (D_job, D_original_job) in zip(LD_jobs, LD_original_jobs):
        for k in D_original_job:
            if k in ["grafana_helpers"]:  # ignore that one
                continue
            assert D_job[k] == D_original_job[k]



def test_single_job_at_random(mtclient, fake_data):
    """
    This job entry should be present in the database.
    """
    # sanity check because the test doesn't make sense if fake data is empty
    assert fake_data['jobs']
    # picking a random one seems like a good choice, instead of always
    # the first one, but the non-deterministic aspect of it is not good
    original_D_job = random.choice(fake_data['jobs'])

    D_job = mtclient.jobs_one(job_id=original_D_job['job_id'])

    for k in original_D_job:
        # That "grafana_helpers" is just pollution in the original data,
        # and we're stripping it automatically in clockwork_web, so this
        # is why we won't see it here.
        if k in ["grafana_helpers", "best_guess_for_username"]:
            continue
        assert D_job[k] == original_D_job[k], f"{D_job}\n{original_D_job}"


def test_single_job_missing(mtclient, fake_data):
    """
    This job entry should be missing from the database.
    """
    # Make sure you pick a random job_id that's not in the database.
    S_job_ids = set([D_job['job_id'] for D_job in fake_data['jobs']])
    while True:
        # let's move towards having all job_id be strings
        job_id = str(int(random.random()*1e7))
        if job_id not in S_job_ids:
            break

    D_job = mtclient.jobs_one(job_id=job_id)
    assert D_job == {}