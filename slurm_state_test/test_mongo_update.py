from slurm_state.mongo_update import *
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config

# Import jobs and nodes parsers
from slurm_state.parsers.job_parser import JobParser
from slurm_state.parsers.node_parser import NodeParser

# Common imports
from datetime import datetime
import pytest


def test_fetch_slurm_report_jobs():
    res = list(
        fetch_slurm_report(
            JobParser("cedar", slurm_version="23.02.6"),  # parser
            "slurm_state_test/files/sacct_1",  # report path
        )
    )

    assert res == [
        {
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
            "end_time": None,
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
        },
        {
            "job_id": "20",
            "array_job_id": "2",
            "array_task_id": "0",
            "name": "test-job-2",
            "username": "nobody2",
            "account": "def-cerise-rrg",
            "job_state": "REQUEUED",
            "exit_code": "SUCCESS:0",
            "time_limit": 1440,
            "submit_time": 1680127990,
            "start_time": 1680127992,
            "end_time": 1680215981,
            "partition": "partition2",
            "nodes": "cdr2",
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
            "working_directory": "/scratch/nobody2",
            "cluster_name": "cedar",
        },
    ]


def test_fetch_slurm_report_nodes():
    res = list(
        fetch_slurm_report(
            NodeParser("mila", slurm_version="22.05.9"),
            "slurm_state_test/files/sinfo_1",
        )
    )
    assert res == [
        {
            "arch": "x86_64",
            "comment": "This is a comment",
            "cores": 2,
            "cpus": 2,
            "last_busy": 1681387881,
            "features": "test_features",
            "gres": "gpu:1",
            "gres_used": "gpu:0,tpu:0",
            "name": "test-node-1",
            "addr": "test-node-1",
            "state": "down",
            "state_flags": ["NOT_RESPONDING"],
            "memory": 1800,
            "reason": "Not responding",
            "reason_changed_at": 1667084449,
            "tres": "cpu=2,mem=1800M,billing=2",
            "tres_used": None,
            "cluster_name": "mila",
        },
        {
            "arch": "",
            "comment": "",
            "cores": 2,
            "cpus": 2,
            "last_busy": 1681387881,
            "features": "other_test_features",
            "gres": None,
            "gres_used": "gpu:0,tpu:0",
            "name": "test-node-2",
            "addr": "test-node-2",
            "state": "down",
            "state_flags": ["DRAIN"],
            "memory": 1800,
            "reason": "Sanity Check Failed",
            "reason_changed_at": 1679695882,
            "tres": "cpu=2,mem=1800M,billing=2",
            "tres_used": "cpu=1",
            "cluster_name": "mila",
        },
    ]


def test_slurm_job_to_clockwork_job():
    job = {
        "name": "sh",
        "username": "testuser",
        "cluster_name": "beluga",
    }
    cw_job = slurm_job_to_clockwork_job(job)
    assert cw_job == {
        "slurm": {
            "name": "sh",
            "username": "testuser",
            "cluster_name": "beluga",
        },
        "cw": {
            "mila_email_username": None,
        },
        "user": {},
    }


def test_slurm_node_to_clockwork_node():
    """
    Test the function slurm_node_to_clockwork_node.
    """

    # Check a minimalist node
    node = {"name": "testnode"}
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {"slurm": {"name": "testnode"}, "cw": {"gpu": {}}}

    # Check a complete node
    node = {
        "name": "test-node",
        "arch": "x86_64",
        "features": "x86_64,turing,48gb",
        "gres": "gpu:rtx8000:8(S:0-1)",
        "addr": "test-node",
        "memory": 386619,
        "state": "MIXED",
        "cfg_tres": "cpu=80,mem=386619M,billing=136,gres/gpu=8",
        "alloc_tres": "cpu=28,mem=192G,gres/gpu=8",
        "comment": None,
        "cluster_name": "beluga",
    }
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {
        "slurm": {
            "name": "test-node",
            "arch": "x86_64",
            "features": "x86_64,turing,48gb",
            "gres": "gpu:rtx8000:8(S:0-1)",
            "addr": "test-node",
            "memory": 386619,
            "state": "MIXED",
            "cfg_tres": "cpu=80,mem=386619M,billing=136,gres/gpu=8",
            "alloc_tres": "cpu=28,mem=192G,gres/gpu=8",
            "comment": None,
            "cluster_name": "beluga",
        },
        "cw": {
            "gpu": {
                "cw_name": "rtx8000",
                "name": "rtx8000",
                "number": 8,
                "associated_sockets": "0-1",
            }
        },
    }

    # Check a node for which the GPU name is not the same in the Slurm report
    # than in the Clockwork convention
    node = {"name": "test2", "features": "x86_64,volta,32gb", "gres": "gpu:v100:4"}
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {
        "slurm": {
            "name": "test2",
            "features": "x86_64,volta,32gb",
            "gres": "gpu:v100:4",
        },
        "cw": {"gpu": {"cw_name": "v100l", "name": "v100", "number": 4}},
    }


def test_main_read_jobs_and_update_collection():
    client = get_mongo_client()
    db = client[get_config("mongo.database_name")]

    db.drop_collection("test_jobs")

    main_read_report_and_update_collection(
        "jobs",
        db.test_jobs,
        db.test_users,
        "cedar",
        "slurm_state_test/files/sacct_1",
        from_file=True,
    )

    assert db.test_jobs.count_documents({}) == 2

    main_read_report_and_update_collection(
        "jobs",
        db.test_jobs,
        db.test_users,
        "cedar",
        "slurm_state_test/files/sacct_2",
        from_file=True,
    )

    assert db.test_jobs.count_documents({}) == 3

    db.drop_collection("test_jobs")


def test_main_read_nodes_and_update_collection():
    client = get_mongo_client()
    db = client[get_config("mongo.database_name")]

    db.drop_collection("test_nodes")

    main_read_report_and_update_collection(
        "nodes",
        db.test_nodes,
        None,
        "mila",
        "slurm_state_test/files/sinfo_1",
        from_file=True,
    )

    assert db.test_nodes.count_documents({}) == 2

    main_read_report_and_update_collection(
        "nodes",
        db.test_nodes,
        None,
        "mila",
        "slurm_state_test/files/sinfo_2",
        from_file=True,
    )

    assert db.test_nodes.count_documents({}) == 3

    db.drop_collection("test_nodes")
