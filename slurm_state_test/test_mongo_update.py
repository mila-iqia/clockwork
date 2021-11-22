from slurm_state.mongo_update import *

import pytest


def test_fetch_slurm_report():
    res = list(
        fetch_slurm_report_nodes(
            "slurm_state_test/files/test_cluster.json",
            "slurm_state_test/files/small_scontrol_node",
        )
    )
    assert res == [
        {
            "name": "test-node",
            "arch": "x86_64",
            "features": "x86_64,turing,48gb",
            "gres": "gpu:rtx8000:8(S:0-1)",
            "addr": "test-node",
            "memory": "386619",
            "state": "MIXED",
            "cfg_tres": "cpu=80,mem=386619M,billing=136,gres/gpu=8",
            "alloc_tres": "cpu=28,mem=192G,gres/gpu=8",
            "comment": None,
            "cluster_name": "test_cluster",
        }
    ]
    res = list(
        fetch_slurm_report_jobs(
            "slurm_state_test/files/test_cluster.json",
            "slurm_state_test/files/small_scontrol_job",
        )
    )
    assert res == [
        {
            "job_id": "1",
            "name": "sh",
            "test_cluster_username": "nobody",
            "account": "clustergroup",
            "job_state": "PENDING",
            "exit_code": "0:0",
            "time_limit": 604800,
            "submit_time": "2020-12-15T16:44:08-05:00",
            "start_time": "Unknown",
            "end_time": "Unknown",
            "partition": "long",
            "nodes": None,
            "command": None,
            "work_dir": "/home/user",
            "cluster_name": "test_cluster",
        }
    ]


def test_slurm_job_to_clockwork_job():
    job = {"name": "sh", "mila_account_username": "testuser"}
    cw_job = slurm_job_to_clockwork_job(job)
    assert cw_job == {
        "slurm": {"name": "sh", "mila_account_username": "testuser"},
        "cw": {
            "cc_account_username": None,
            "mila_account_username": "testuser",
            "mila_email_username": None,
        },
        "user": {},
    }


def test_slurm_node_to_clockwork_node():
    node = {"name": "testnode"}
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {"slurm": {"name": "testnode"}, "cw": {}}
