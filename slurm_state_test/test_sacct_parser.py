# Setup tests based on test_sacct_parser.py and test_scontrol_parser.py
# to parse the SAME data but from a mocked ssh sacct call,
# from DRAC and Mila clusters

# the file sacct_1 was obtained from cedar with the command:
# /opt/software/slurm/bin/sacct -A rrg-bengioy-ad_gpu,rrg-bengioy-ad_cpu,def-bengioy_gpu,def-bengioy_cpu -X -S 2023-03-30T00:00 -E 2023-03-31T00:00 --json

from slurm_state.sacct_parser import *


def test_job_parser():
    f = open("slurm_state_test/files/sacct_1")

    jobs = list(job_parser(f))

    job_0 = {
        "job_id": "10",
        "array_job_id": "1",
        "array_task_id": "7",
        "name": "test-job-1",
        "username": "nobody",
        "account": "def-cerise-rrg",
        "job_state": "NODE_FAIL",
        "exit_code": "SUCCESS:0",
        "time_limit": 1440,
        "submit_time": 1680193479,
        "start_time": 1680193504,
        "end_time": 1680244103,
        "partition": "partition1",
        "nodes": "cdr1",
        "tres_allocated": {
            "mem": 40960,
            "billing": 1,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1,
        },
        "tres_requested": {
            "mem": 40960,
            "billing": 1,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1,
        },
        "working_directory": "/scratch/nobody",
        "cluster_name": "cedar",
    }
    assert jobs[0] == job_0
    assert jobs[1]["job_id"] == "20"
