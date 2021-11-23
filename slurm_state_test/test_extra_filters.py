import pytest

from slurm_state.extra_filters import (
    is_allocation_related_to_mila,
    extract_username_from_slurm_fields,
)


def test_filtering_allocations():
    """
    This tests the filtering function that lets through only the jobs
    from the allocations related to Mila, as defined by the file
    "fake_allocations_related_to_mila.json".
    Outside of testing time, there is a file that contains legitimate values.
    """
    LD_jobs = [
        {
            "slurm": {"account": "some_invalid_string1", "job_id": "0000"},
            "cw": {},
            "user": {},
        },
        {
            "slurm": {"account": "valid_fake_allocation_name", "job_id": "1111"},
            "cw": {},
            "user": {},
        },
        {
            "slurm": {"account": "valid_fake_allocation_name", "job_id": "2222"},
            "cw": {},
            "user": {},
        },
        {
            "slurm": {"account": "some_invalid_string2", "job_id": "4444"},
            "cw": {},
            "user": {},
        },
    ]
    LD_jobs_out = list(filter(is_allocation_related_to_mila, LD_jobs))
    assert len(LD_jobs_out) == 2
    for D_job in LD_jobs_out:
        assert D_job["slurm"]["job_id"] in ["1111", "2222"]


def test_single_extract_username_from_slurm_fields():
    """
    Make sure all the cases detailed in the code are covered.
    This is to make sure that our battery of regex actually catch
    what they purport to catch.
    """

    for (k, v, truth) in [
        ("command", "/home/mila/s/summbuf/", "summbuf"),
        ("std_err", "/home/mila/s/summbuf/randomsearch_90.log", "summbuf"),
        ("work_dir", "/home/mila/b/buffy.summers", "buffy.summers"),
        ("std_out", "/home/mila/s/summbuf/randomsearch_90.log", "summbuf"),
        ("work_dir", "/home/mila/b/buffy.summers", "buffy.summers"),
        ("command", "/network/tmp1/buffy.summers/git/a/job.sh 0.1", "buffy.summers"),
        ("work_dir", "/network/tmp1/buffy.summers", "buffy.summers"),
        (
            "work_dir",
            "/network/data2/tech-transfer/summbuf/some_project/neurips/bleh",
            "summbuf",
        ),
        ("work_dir", "/network/data2/tech-transfer/summbuf/some_project", "summbuf"),
        ("work_dir", "/network/data2/tech-transfer/summbuf", "summbuf"),
        ("work_dir", "/scratch/summbuf/log/data/treehouse", "summbuf"),
        ("std_err", "/scratch/summbuf/log/data/treehouse/gamma-000.err", "summbuf"),
        ("std_out", "/scratch/summbuf/log/data/treehouse/gamma-000.out", "summbuf"),
        (
            "std_err",
            "/lustre03/project/1111111/summbuf/treehouse/slurm-19741310.out",
            "summbuf",
        ),
        (
            "std_out",
            "/lustre03/project/1111111/summbuf/treehouse/slurm-19741310.out",
            "summbuf",
        ),
        ("work_dir", "/lustre03/project/1111111/summbuf/treehouse", "summbuf"),
        ("command", "/home/summbuf/", "summbuf"),
        ("std_err", "/home/summbuf/treehouse/logs/allo.out", "summbuf"),
        ("std_out", "/home/summbuf/treehouse/logs/allo.out", "summbuf"),
        ("work_dir", "/home/summbuf/treehouse", "summbuf"),
        (
            "std_err",
            "/lustre04/scratch/summbuf/treehouse/separate_layers/allo/slurm-1111.out",
            "summbuf",
        ),
        (
            "std_out",
            "/lustre04/scratch/summbuf/treehouse/separate_layers/allo/slurm-1111.out",
            "summbuf",
        ),
        (
            "command",
            "/lustre04/scratch/summbuf/code/treehouse/scripts/train",
            "summbuf",
        ),
        ("work_dir", "/home/summbuf", "summbuf"),
        ("work_dir", "/home/buffy_summers", "buffy_summers"),
        ("work_dir", "/lustre04/scratch/summbuf/allo", "summbuf"),
        ("work_dir", "/lustre04/scratch/summbuf/bye/src", "summbuf"),
        # this one is more subtle, and the answer is NOT "mila"
        ("work_dir", "/home/mila/s/summbuf/Github/allo", "summbuf"),
    ]:
        assert extract_username_from_slurm_fields({k: v}) == truth


def test_voting_extract_username_from_slurm_fields():
    """
    If there is any confusion with many possibilities,
    vote and return the most common value.
    """
    assert (
        extract_username_from_slurm_fields(
            {
                "work_dir": "/home/user1",
                "command": "/home/user2/",
                "std_out": "/home/user2/logs/allo.out",
            }
        )
        == "user2"
    )


def test_nobody_extract_username_from_slurm_fields():
    """
    Make sure we get "unknown" when nothing gives us hints.
    """
    assert (
        extract_username_from_slurm_fields(
            {
                "work_dir": "/bleh",
                "command": "/g/goldorak",
                "std_err": "",
                "std_out": "",
            }
        )
        == "unknown"
    )
