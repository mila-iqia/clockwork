# Setup tests based on test_sacct_parser.py and test_scontrol_parser.py
# to parse the SAME data but from a mocked ssh sacct call,
# from DRAC and Mila clusters

# the file sacct_1 was obtained from cedar with the command:
# /opt/software/slurm/bin/sacct -A rrg-bengioy-ad_gpu,rrg-bengioy-ad_cpu,def-bengioy_gpu,def-bengioy_cpu -X -S 2023-03-30T00:00 -E 2023-03-31T00:00 --json

from slurm_state.sacct_parser import *


def test_job_parser():
    f = open("slurm_state_test/files/sacct_1")

    jobs = job_parser(f)

    # fields to test:

    # job_id "1234"
    # name "interactive"
    # username "nobody"
    # account "mila"
    # job_state "FAILED"
    # exit_code "1:0"
    # time_limit 43200
    # submit_time 1667708757
    # start_time 1678930026
    # end_time 1678930037
    # partition "main"
    # nodes "cn-d003"
    # num_nodes "1"
    # num_cpus "6"
    # num_tasks "1"
    # cpus_per_task "6"
    # TRES "cpu=6,mem=32G,node=1,billing=4,gres/gpu=2"
    # command null
    # work_dir "/home/mila/n/nobody"
    # tres_per_node "gres:gpu:a100:2"
    # cluster_name "mila"

    # TODO: avec et sans array
    job_0 = {
        "job_id": 63768795,
        "array_job_id": 63752790,  # OK
        "array_task_id": 7,  # OK
        "name": "submitit",
        "username": "nobody",
        "account": "rrg-cerise-ad_gpu",  # OK
        "job_state": "NODE_FAIL",
        "exit_code": "SUCCESS:0",  # ?
        "time_limit": 1440,  # OK
        "submit_time": 1680193479,  # OK
        "start_time": 1680193504,  # OK
        "end_time": 1680244103,  # OK
        "partition": "gpubase_bygpu_b3",
        "nodes": "cdr247",
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
        # "num_nodes": 1,  # ?
        # "num_cpus": 4,  # ?
        # "num_tasks": 1,  # ?
        # "cpus_per_task": 4,  # ?
        # "TRES": "cpu=4,mem=40G,node=1,billing=1,gres/gpu=1",
        "working_directory": "/scratch/nobody",
        # "tres_per_node": "gres:gpu:1001:1",  # ?
        "cluster_name": "cedar",  # OK
    }

    # the following test code is temporary, while developping the tested fucntion;
    # eventually it will become something like a simple comparison between job_0 and jobs[0]

    print(jobs[0])

    for k, v in job_0.items():
        print(f'testing value "{k}"="{v}"')
        assert jobs[0][k] == v
    for k, v in jobs[0].items():
        assert job_0[k] == v

    assert jobs[0]["job_id"] == 63768795

    assert jobs[1]["job_id"] == 63694682
