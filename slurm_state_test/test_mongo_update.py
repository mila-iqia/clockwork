from slurm_state.mongo_update import *
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config

from datetime import datetime

import pytest


def test_fetch_slurm_report():
    res = list(
        fetch_slurm_report_nodes(
            "test_cluster",
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
            "memory": 386619,
            "state": "MIXED",
            "cfg_tres": "cpu=80,mem=386619M,billing=136,gres/gpu=8",
            "alloc_tres": "cpu=28,mem=192G,gres/gpu=8",
            "comment": None,
            "cluster_name": "test_cluster",
        }
    ]
    res = list(
        fetch_slurm_report_jobs(
            "test_cluster",
            "slurm_state_test/files/small_scontrol_job",
        )
    )
    assert res == [
        {
            "job_id": "1",
            "name": "sh",
            "test_cluster_username": "nobody",
            "uid": 65535,
            "account": "clustergroup",
            "job_state": "PENDING",
            "exit_code": "0:0",
            "time_limit": 604800,
            "submit_time": datetime.fromisoformat(
                "2020-12-15T16:44:08-05:00"
            ).timestamp(),
            "start_time": None,
            "end_time": None,
            "partition": "long",
            "nodes": None,
            "num_nodes": "1",
            "num_cpus": "1",
            "num_tasks": "1",
            "cpus_per_task": "1",
            "TRES": "cpu=1,mem=2G,node=1,gres/gpu=1",
            "tres_per_node": "gpu:titanxp:1",
            "command": None,
            "work_dir": "/home/user",
            "cluster_name": "test_cluster",
        }
    ]


def test_slurm_job_to_clockwork_job():
    job = {
        "name": "sh",
        "test_cluster_username": "testuser",
        "cluster_name": "test_cluster",
    }
    cw_job = slurm_job_to_clockwork_job(job)
    assert cw_job == {
        "slurm": {
            "name": "sh",
            "test_cluster_username": "testuser",
            "cluster_name": "test_cluster",
        },
        "cw": {
            "mila_email_username": None,
        },
        "user": {},
    }


def test_slurm_node_to_clockwork_node():
    node = {"name": "testnode"}
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {"slurm": {"name": "testnode"}, "cw": {}}


def test_main_read_jobs_and_update_collection():
    client = get_mongo_client()
    db = client[get_config("mongo.database_name")]

    db.drop_collection("test_jobs")

    main_read_jobs_and_update_collection(
        db.test_jobs,
        db.test_users,
        "test_cluster",
        "slurm_state_test/files/small_scontrol_job",
    )

    assert db.test_jobs.count_documents({}) == 1

    main_read_jobs_and_update_collection(
        db.test_jobs,
        db.test_users,
        "test_cluster",
        "slurm_state_test/files/scontrol_job_2",
    )

    assert db.test_jobs.count_documents({}) == 2

    db.drop_collection("test_jobs")


def test_main_read_nodes_and_update_collection():
    client = get_mongo_client()
    db = client[get_config("mongo.database_name")]

    db.drop_collection("test_nodes")

    main_read_nodes_and_update_collection(
        db.test_nodes,
        "test_cluster",
        "slurm_state_test/files/small_scontrol_node",
    )

    assert db.test_nodes.count_documents({}) == 1

    main_read_nodes_and_update_collection(
        db.test_nodes,
        "test_cluster",
        "slurm_state_test/files/scontrol_node_2",
    )

    assert db.test_nodes.count_documents({}) == 2

    db.drop_collection("test_nodes")
