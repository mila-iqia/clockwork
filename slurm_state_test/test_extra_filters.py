import pytest

from slurm_state.extra_filters import (
    is_allocation_related_to_mila,
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
            "slurm": {
                "account": "some_invalid_string1",
                "job_id": "0000",
                "cluster_name": "narval",
            },
            "cw": {},
            "user": {},
        },
        {
            "slurm": {
                "account": "def-pomme-rrg",  # Valid fake allocation name
                "job_id": "1111",
                "cluster_name": "graham",
            },
            "cw": {},
            "user": {},
        },
        {
            "slurm": {
                "account": "some_arbitrary_string",
                "job_id": "2222",
                "cluster_name": "mila",
            },
            "cw": {},
            "user": {},
        },
        {
            "slurm": {
                "account": "some_invalid_string2",
                "job_id": "4444",
                "cluster_name": "narval",
            },
            "cw": {},
            "user": {},
        },
    ]
    LD_jobs_out = list(filter(is_allocation_related_to_mila, LD_jobs))
    assert len(LD_jobs_out) == 2
    for D_job in LD_jobs_out:
        assert D_job["slurm"]["job_id"] in ["1111", "2222"]
