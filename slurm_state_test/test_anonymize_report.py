"""
Tests related to the file slurm_state.anonymize_report
"""

import json

from slurm_state.anonymize_report import anonymize_job, anonymize_node


def test_anonymize_job():

    D_cluster_account = {
        "username": "some_user",
        "uid": 10000,
        "account": "mila",
        "cluster_name": "mila",
    }

    D_input_job = {
        "account": "mila",
        "comment": {"administrator": None, "job": None, "system": None},
        "allocation_nodes": 1,
        "array": {
            "job_id": 123456,
            "limits": {"max": {"running": {"tasks": 0}}},
            "task": 123456,
            "task_id": 42,
        },
        "association": {
            "account": "secret",
            "cluster": "mila",
            "partition": "secret",
            "user": "secret",
        },
        "cluster": "mila",
        "constraints": "x86_64",
        "derived_exit_code": {"status": "SUCCESS", "return_code": 0},
        "time": {
            "elapsed": 217,
            "eligible": 1686088321,
            "end": 1686219300,
            "start": 1686088321,
            "submission": 1686088315,
            "suspended": 0,
            "system": {"seconds": 0, "microseconds": 0},
            "limit": 4320,
            "total": {"seconds": 0, "microseconds": 0},
            "user": {"seconds": 0, "microseconds": 0},
        },
        "exit_code": {"status": "SUCCESS", "return_code": 0},
        "flags": ["CLEAR_SCHEDULING", "STARTED_ON_BACKFILL"],
        "group": "secret",
        "het": {"job_id": 0, "job_offset": None},
        "job_id": 123456,
        "name": "secret",
        "mcs": {"label": ""},
        "nodes": "thisisanode",
        "partition": "long",
        "priority": 911,
        "qos": "normal",
        "required": {"CPUs": 8, "memory": 98304},
        "kill_request_user": None,
        "reservation": {"id": 0, "name": 0},
        "state": {"current": "FAILED", "reason": "Prolog"},
        "steps": [],
        "tres": {
            "allocated": [
                {"type": "cpu", "name": None, "id": 1, "count": 8},
                {"type": "mem", "name": None, "id": 2, "count": 98304},
                {"type": "node", "name": None, "id": 4, "count": 1},
                {"type": "billing", "name": None, "id": 5, "count": 2},
                {"type": "gres", "name": "gpu", "id": 1001, "count": 1},
            ],
            "requested": [
                {"type": "cpu", "name": None, "id": 1, "count": 8},
                {"type": "mem", "name": None, "id": 2, "count": 98304},
                {"type": "node", "name": None, "id": 4, "count": 1},
                {"type": "billing", "name": None, "id": 5, "count": 2},
                {"type": "gres", "name": "gpu", "id": 1001, "count": 1},
            ],
        },
        "user": "secret",
        "wckey": {"wckey": "", "flags": []},
        "working_directory": "secret",
    }

    D_anonymized_job = json.dumps(anonymize_job(D_input_job, D_cluster_account))
    assert "secret" not in D_anonymized_job
    assert "123456" not in D_anonymized_job


def test_anonymize_node():

    D_user = {
        "cluster_name": "mila",
    }

    D_input_node = {
        "architecture": "this_is_an_architecture",
        "burstbuffer_network_address": "",
        "boards": 1,
        "boot_time": 0,
        "comment": "",
        "cores": 2,
        "cpu_binding": 0,
        "cpu_load": 4294967294,
        "extra": "",
        "free_memory": -2,
        "cpus": 2,
        "last_busy": 1684425426,
        "features": "",
        "active_features": "",
        "gres": "",
        "gres_drained": "N/A",
        "gres_used": "gpu:0,tpu:0",
        "mcs_label": "",
        "name": "thisisaname",
        "next_state_after_reboot": "invalid",
        "address": "thisisaname",
        "hostname": "thisisaname",
        "state": "down",
        "state_flags": ["NOT_RESPONDING"],
        "next_state_after_reboot_flags": [],
        "operating_system": "secret",
        "owner": None,
        "partitions": ["secret"],
        "port": 6116,
        "real_memory": 1800,
        "reason": "secret",
        "reason_changed_at": 1667084449,
        "reason_set_by_user": "secret",
        "slurmd_start_time": 0,
        "sockets": 1,
        "threads": 1,
        "temporary_disk": 0,
        "weight": 1,
        "tres": "cpu=2,mem=1800M,billing=2",
        "slurmd_version": "",
        "alloc_memory": 0,
        "alloc_cpus": 0,
        "idle_cpus": 2,
        "tres_used": None,
    }

    assert "secret" not in json.dumps(anonymize_node(D_input_node, D_user))
