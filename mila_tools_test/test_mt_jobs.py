
import random


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
        job_id = int(random.random()*1e7)
        if job_id not in S_job_ids:
            break

    D_job = mtclient.jobs_one(job_id=job_id)
    assert D_job == {}