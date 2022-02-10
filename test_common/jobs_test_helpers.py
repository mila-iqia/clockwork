"""
Many tests had duplicated logic in
    test_mt_jobs.py
    test_rest_jobs.py
    test_browser_jobs.py
because the same tests were performed at different locations
to flex different ways to access the information on the server.

As much as possible, we have put here the common logic
and we export it to those respective files.

It is less obvious how to do that with "test_browser_jobs.py"
because it would involve testing the contents of the rendered
html pages, which are not necessarily meant to display all
the information.
"""


import random
import time
import copy


def helper_single_job_at_random(fake_data, cluster_name):

    original_D_job = random.choice(
        [
            D_job
            for D_job in fake_data["jobs"]
            if D_job["slurm"]["cluster_name"] == cluster_name
        ]
    )
    job_id = original_D_job["slurm"]["job_id"]

    def validator(D_job):

        for k1 in original_D_job:
            assert k1 in ["slurm", "cw", "user"]
            for k2 in original_D_job[k1]:
                if k2 in ["best_guess_for_username"]:
                    continue
                assert (
                    D_job[k1][k2] == original_D_job[k1][k2]
                ), f"{D_job}\n{original_D_job}"

    return validator, job_id


def helper_single_job_missing(fake_data):
    """
    Helper function to make a request to the REST API
    endpoint /api/v1/clusters/jobs/one, and to mtclient.jobs_one.

    This job entry should be missing from the database.
    """

    # Make sure you pick a random job_id that's not in the database.
    S_job_ids = set([D_job["slurm"]["job_id"] for D_job in fake_data["jobs"]])
    while True:
        job_id = "absent_job_%d" % int(random.random() * 1e7)
        if job_id not in S_job_ids:
            break

    def validator(D_job):
        assert D_job == {}

    return validator, job_id


def helper_list_relative_time(fake_data):
    """
    Make a request to the REST API endpoint /api/v1/clusters/jobs/list.

    Since we have access to the `fake_data` we can make sure that all the
    corresponding entries are indeed returned. We can also use that to pick
    a query value that's sure to return something, because the `fake_data`
    contains jobs that are static and not very recent (i.e. asking for "everything
    that ended earlier than an hour ago" would return nothing except jobs
    that have "end_time" as `None`).
    """

    L_end_times = list(
        sorted(
            [
                D_job["slurm"]["end_time"]
                for D_job in fake_data["jobs"]
                if D_job["slurm"]["end_time"] is not None
            ]
        )
    )
    N = len(L_end_times)
    assert 10 <= N
    # Adding a +1 second because we don't want to balance on the edge
    # of whether $gt is inclusive or not in mongodb.
    # This isn't the point, so we add a +1.
    mid_end_time = L_end_times[N // 2] + 1

    # now let's find the ground truth
    LD_jobs_ground_truth = [
        D_job
        for D_job in fake_data["jobs"]
        if (D_job["slurm"]["end_time"] is None)
        or (mid_end_time <= D_job["slurm"]["end_time"])
    ]

    relative_mid_end_time = time.time() - mid_end_time
    assert 0 < relative_mid_end_time

    def validator(LD_jobs_results):
        # Compare with ground truth. Let's just compare the "job_id"
        # of the jobs returned in both situations.
        assert set([D_job["slurm"]["job_id"] for D_job in LD_jobs_ground_truth]) == set(
            [D_job["slurm"]["job_id"] for D_job in LD_jobs_results]
        )

    return validator, relative_mid_end_time


def helper_list_jobs_for_a_given_random_user(fake_data):

    """
    Helper function to make a request to the REST API
    endpoint /api/v1/clusters/jobs/list, and to mtclient.jobs_list.

    We pick a user at random from our fake_data, and we see if we
    can list the jobs for that user.
    """

    def get_ground_truth(username, LD_jobs):
        return [
            D_job
            for D_job in LD_jobs
            if username
            in [
                D_job["cw"].get("mila_cluster_username", None),
                D_job["cw"].get("mila_email_username", None),
                D_job["cw"].get("cc_account_username", None),
            ]
        ]

    # Select something at random from the database, already populated
    # by the fake_data, in order to construct a good request.

    # Instead of drawing a random user with replacements until
    # we hit a good one, we'll just shuffle the list and iterate
    # until we hit a good one.

    LD_users = copy.copy(fake_data["users"])
    random.shuffle(LD_users)
    for D_user in LD_users:
        L_username = [D_user["mila_cluster_username"], D_user["cc_account_username"]]
        random.shuffle(L_username)
        for username in L_username:
            LD_jobs_ground_truth = get_ground_truth(username, fake_data["jobs"])
            # pick something that's interesting, and not something that should
            # return empty results, because then this test becomes vacuous
            if LD_jobs_ground_truth:
                continue
    assert (
        LD_jobs_ground_truth
    ), f"Failed to get an interesting test candidate for helper_list_jobs_for_a_given_random_user. We hit the safety valve."

    # response = client.get(
    #    f"/api/v1/clusters/jobs/list?user={username}", headers=valid_rest_auth_headers
    # )
    # assert response.content_type == "application/json"
    # LD_jobs = response.get_json()

    def validator(LD_jobs):
        # make sure that every job returned has that username somewhere
        for D_job in LD_jobs:
            assert username in [
                D_job["cw"].get("mila_cluster_username", None),
                D_job["cw"].get("mila_email_username", None),
                D_job["cw"].get("cc_account_username", None),
            ]

        # Let's just make sure that the set of job_id match for both the returned
        # results and the ground truth.
        # We could do an in-depth comparison with all the fields, but that seems
        # a bit zealous for now.
        assert set(D_job["slurm"]["job_id"] for D_job in LD_jobs) == set(
            D_job["slurm"]["job_id"] for D_job in LD_jobs_ground_truth
        )

    return validator, username


def helper_jobs_list_with_filter(fake_data, cluster_name):
    """
    Test the `jobs_list` command. This is just to make sure that the filtering works
    and the `cluster_name` argument is functional.
    """

    LD_original_jobs = [
        D_job
        for D_job in fake_data["jobs"]
        if D_job["slurm"]["cluster_name"] == cluster_name
    ]
    LD_original_jobs = list(
        sorted(LD_original_jobs, key=lambda D_job: D_job["slurm"]["job_id"])
    )

    def validator(LD_jobs):

        assert len(LD_jobs) == len(LD_original_jobs), (
            "Lengths of lists don't match, so we shouldn't expect them to be able "
            "to match the elements themselves."
        )
        # agree on some ordering so you can zip the lists and have
        # matching elements in the same order
        LD_jobs = list(sorted(LD_jobs, key=lambda D_job: D_job["slurm"]["job_id"]))
        # compare all the dicts one by one
        for (D_job, D_original_job) in zip(LD_jobs, LD_original_jobs):
            for k1 in D_original_job:
                assert k1 in ["slurm", "cw", "user"]
                for k2 in D_original_job[k1]:
                    if k2 in ["best_guess_for_username"]:
                        continue
                    assert D_job[k1][k2] == D_original_job[k1][k2]

    return validator
