from slurm_state.mongo_update import *
from slurm_state.mongo_client import get_mongo_client

from datetime import datetime

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
            "slurm_state_test/files/test_cluster.json",
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
        "mila_cluster_username": "testuser",
        "cluster_name": "test_cluster",
    }
    cw_job = slurm_job_to_clockwork_job(job)
    assert cw_job == {
        "slurm": {
            "name": "sh",
            "mila_cluster_username": "testuser",
            "cluster_name": "test_cluster",
        },
        "cw": {
            "cc_account_username": None,
            "mila_cluster_username": "testuser",
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
    assert cw_node == {"slurm": {"name": "testnode"}, "cw": {"gpu":{}}}

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
        "cluster_name": "test_cluster",
    }
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {"slurm": {
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
                        },
                        "cw": {
                            "gpu": {
                                "cw_name": "rtx8000",
                                "name": "rtx8000",
                                "number": 8,
                                "associated_sockets": "0-1"
                            }
                        }
                    }

    # Check a node for which the GPU name is not the same in the Slurm report
    # than in the Clockwork convention
    node = {
        "name": "test2",
        "features": "x86_64,volta,32gb",
        "gres": "gpu:v100:4"
    }
    cw_node = slurm_node_to_clockwork_node(node)
    assert cw_node == {
        "slurm": {
            "name": "test2",
            "features": "x86_64,volta,32gb",
            "gres": "gpu:v100:4"
        },
        "cw": {
            "gpu": {
                "cw_name": "v100l",
                "name": "v100",
                "number": 4
            }
        }
    }

def test_main_read_jobs_and_update_collection():
    client = get_mongo_client(os.environ["MONGODB_CONNECTION_STRING"])
    db = client[os.environ["MONGODB_DATABASE_NAME"]]

    db.drop_collection("test_jobs")

    main_read_jobs_and_update_collection(
        db.test_jobs,
        db.test_users,
        "slurm_state_test/files/test_cluster.json",
        "slurm_state_test/files/small_scontrol_job",
    )

    assert db.test_jobs.count_documents({}) == 1

    main_read_jobs_and_update_collection(
        db.test_jobs,
        db.test_users,
        "slurm_state_test/files/test_cluster.json",
        "slurm_state_test/files/scontrol_job_2",
    )

    assert db.test_jobs.count_documents({}) == 2

    db.drop_collection("test_jobs")


def test_main_read_nodes_and_update_collection():
    client = get_mongo_client(os.environ["MONGODB_CONNECTION_STRING"])
    db = client[os.environ["MONGODB_DATABASE_NAME"]]

    db.drop_collection("test_nodes")

    main_read_nodes_and_update_collection(
        db.test_nodes,
        "slurm_state_test/files/test_cluster.json",
        "slurm_state_test/files/small_scontrol_node",
    )

    assert db.test_nodes.count_documents({}) == 1

    main_read_nodes_and_update_collection(
        db.test_nodes,
        "slurm_state_test/files/test_cluster.json",
        "slurm_state_test/files/scontrol_node_2",
    )

    assert db.test_nodes.count_documents({}) == 2

    db.drop_collection("test_nodes")

    # Check for a list of different cases regarding the 'Gres' and
    # 'AvailableFeatures' elements
    main_read_nodes_and_update_collection(
        db.test_nodes,
        "slurm_state_test/files/test_cluster.json",
        "slurm_state_test/files/scontrol_node_3",
    )

    assert db.test_nodes.count_documents({}) == 5

    db.drop_collection("test_nodes")
