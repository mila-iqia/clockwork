
# Examples of data returned by pyslurm on 2021-05-19.

To be used when writing scripts, when you wonder what format the data returned has.

## pyslurm.node().get()

```json
{
    "ci-computenode": {
        "arch": null,
        "boards": 1,
        "boot_time": 0,
        "cores": 2,
        "core_spec_cnt": 0,
        "cores_per_socket": 2,
        "cpus": 2,
        "cpu_load": null,
        "cpu_spec_list": [],
        "features": [],
        "features_active": [],
        "free_mem": null,
        "gres": [],
        "gres_drain": "N/A",
        "gres_used": [
            "gpu:0",
            "tpu:0"
        ],
        "mcs_label": null,
        "mem_spec_limit": 0,
        "name": "ci-computenode",
        "node_addr": "ci-computenode",
        "node_hostname": "ci-computenode",
        "os": null,
        "owner": null,
        "partitions": [
            "debug"
        ],
        "real_memory": 1800,
        "slurmd_start_time": 0,
        "sockets": 1,
        "threads": 1,
        "tmp_disk": 0,
        "weight": 1,
        "tres_fmt_str": "cpu=2,mem=1800M,billing=2",
        "version": null,
        "reason": "Not responding",
        "reason_time": 1621370977,
        "reason_uid": 1111,
        "power_mgmt": {
            "cap_watts": null
        },
        "energy": {
            "current_watts": 0,
            "ave_watts": 0,
            "previous_consumed_energy": 0
        },
        "alloc_cpus": 0,
        "err_cpus": 0,
        "state": "DOWN*",
        "alloc_mem": 0
    },
    "cn-a001": {
        "arch": null,
        "boards": 1,
        "boot_time": 0,
        "cores": 20,
        "core_spec_cnt": 0,
        "cores_per_socket": 20,
        "cpus": 80,
        "cpu_load": null,
        "cpu_spec_list": [],
        "features": "x86_64,turing,48gb",
        "features_active": "x86_64,turing,48gb",
        "free_mem": null,
        "gres": [
            "gpu:rtx8000:8"
        ],
        "gres_drain": "N/A",
        "gres_used": [
            "gpu:rtx8000:0",
            "tpu:0"
        ],
        "mcs_label": null,
        "mem_spec_limit": 0,
        "name": "cn-a001",
        "node_addr": "cn-a001",
        "node_hostname": "cn-a001",
        "os": null,
        "owner": null,
        "partitions": [
            "debug",
            "unkillable",
            "short-unkillable",
            "main",
            "main-grace",
            "long",
            "long-grace",
            "cpu_jobs_low",
            "cpu_jobs_low-grace"
        ],
        "real_memory": 386619,
        "slurmd_start_time": 0,
        "sockets": 2,
        "threads": 2,
        "tmp_disk": 3600000,
        "weight": 1,
        "tres_fmt_str": "cpu=80,mem=386619M,billing=136,gres/gpu=8",
        "version": null,
        "reason": "Not responding",
        "reason_time": 1619727150,
        "reason_uid": 0,
        "power_mgmt": {
            "cap_watts": null
        },
        "energy": {
            "current_watts": 0,
            "ave_watts": 0,
            "previous_consumed_energy": 0
        },
        "alloc_cpus": 0,
        "err_cpus": 0,
        "state": "DOWN*",
        "alloc_mem": 0
    },
    ...
}
```

## pyslurm.job().get()

This is 250k lines so we'll truncate it.

```json
{
    "679166": {
        "account": "mila",
        "accrue_time": "2020-12-15T16:44:08",
        "admin_comment": null,
        "alloc_node": "login-2",
        "alloc_sid": 20721,
        "array_job_id": null,
        "array_task_id": null,
        "array_task_str": null,
        "array_max_tasks": null,
        "assoc_id": 57,
        "batch_flag": 0,
        "batch_features": null,
        "batch_host": null,
        "billable_tres": null,
        "bitflags": 503316480,
        "boards_per_node": 0,
        "burst_buffer": null,
        "burst_buffer_state": null,
        "command": null,
        "comment": null,
        "contiguous": false,
        "core_spec": null,
        "cores_per_socket": null,
        "cpus_per_task": "N/A",
        "cpus_per_tres": null,
        "cpu_freq_gov": null,
        "cpu_freq_max": null,
        "cpu_freq_min": null,
        "dependency": null,
        "derived_ec": "0:0",
        "eligible_time": 1608068648,
        "end_time": 0,
        "exc_nodes": [],
        "exit_code": "0:0",
        "features": [
            "x86_64"
        ],
        "group_id": 1500000048,
        "job_id": 679166,
        "job_state": "PENDING",
        "last_sched_eval": "2020-12-24T00:01:37",
        "licenses": {},
        "max_cpus": 0,
        "max_nodes": 0,
        "mem_per_tres": null,
        "name": "sh",
        "network": null,
        "nodes": null,
        "nice": 0,
        "ntasks_per_core": null,
        "ntasks_per_core_str": "UNLIMITED",
        "ntasks_per_node": 0,
        "ntasks_per_socket": null,
        "ntasks_per_socket_str": "UNLIMITED",
        "ntasks_per_board": 0,
        "num_cpus": 1,
        "num_nodes": 1,
        "num_tasks": 1,
        "partition": "long",
        "mem_per_cpu": true,
        "min_memory_cpu": 2048,
        "mem_per_node": false,
        "min_memory_node": null,
        "pn_min_memory": 2048,
        "pn_min_cpus": 1,
        "pn_min_tmp_disk": 0,
        "power_flags": 0,
        "priority": 0,
        "profile": 0,
        "qos": "normal",
        "reboot": 0,
        "req_nodes": [],
        "req_switch": 0,
        "requeue": true,
        "resize_time": 0,
        "restart_cnt": 0,
        "resv_name": null,
        "run_time": 0,
        "run_time_str": "00:00:00",
        "sched_nodes": null,
        "shared": "OK",
        "show_flags": 18,
        "sockets_per_board": 0,
        "sockets_per_node": null,
        "start_time": 0,
        "state_reason": "BadConstraints",
        "std_err": null,
        "std_in": null,
        "std_out": null,
        "submit_time": 1608068648,
        "suspend_time": 0,
        "system_comment": null,
        "time_limit": 10080,
        "time_limit_str": "7-00:00:00",
        "time_min": 0,
        "threads_per_core": null,
        "tres_alloc_str": null,
        "tres_bind": null,
        "tres_freq": null,
        "tres_per_job": null,
        "tres_per_node": "gpu:titanxp:1",
        "tres_per_socket": null,
        "tres_per_task": null,
        "tres_req_str": "cpu=1,mem=2G,node=1,gres/gpu=1",
        "user_id": 1500000048,
        "wait4switch": 0,
        "wckey": null,
        "work_dir": "/home/mila/b/bouklihg",
        "cpus_allocated": {},
        "cpus_alloc_layout": {}
    },
    ...
}
```


## pyslurm.reservation().get()

This is long, but we can include the whole thing here.

```json
{
    "transtech": {
        "accounts": [],
        "burst_buffer": [],
        "core_cnt": 120,
        "end_time": 1640840400,
        "features": [],
        "flags": "IGNORE_JOBS,SPEC_NODES",
        "licenses": {},
        "node_cnt": 3,
        "node_list": "cn-a[003-004],cn-b005",
        "partition": null,
        "start_time": 1609864382,
        "tres_str": [
            "cpu=240"
        ],
        "users": [
            "germaima",
            "bertranh",
            "blackbus",
            "luckmarg",
            "rishab.goel",
            "fansitca"
        ]
    },
    "chum": {
        "accounts": [],
        "burst_buffer": [],
        "core_cnt": 10,
        "end_time": 1640840400,
        "features": [],
        "flags": "IGNORE_JOBS,SPEC_NODES",
        "licenses": {},
        "node_cnt": 1,
        "node_list": "rtx3",
        "partition": null,
        "start_time": 1612240858,
        "tres_str": [
            "cpu=20"
        ],
        "users": [
            "mamlouka",
            "sinhakou",
            "wabarthm",
            "pagecacl",
            "chen-yang.su"
        ]
    },
    "DGXA100": {
        "accounts": [],
        "burst_buffer": [],
        "core_cnt": 256,
        "end_time": 1640840400,
        "features": [],
        "flags": "IGNORE_JOBS,SPEC_NODES",
        "licenses": {},
        "node_cnt": 2,
        "node_list": "cn-d[001-002]",
        "partition": null,
        "start_time": 1617232641,
        "tres_str": [
            "cpu=512"
        ],
        "users": [
            "mamlouka",
            "bilaniuo"
        ]
    },
    "cn-c": {
        "accounts": [],
        "burst_buffer": [],
        "core_cnt": 128,
        "end_time": 1640840400,
        "features": [],
        "flags": "IGNORE_JOBS,SPEC_NODES",
        "licenses": {},
        "node_cnt": 2,
        "node_list": "cn-c[001,036]",
        "partition": null,
        "start_time": 1617232709,
        "tres_str": [
            "cpu=128"
        ],
        "users": [
            "mamlouka"
        ]
    },
    "badrinaa": {
        "accounts": [],
        "burst_buffer": [],
        "core_cnt": 64,
        "end_time": 1640840400,
        "features": [],
        "flags": "IGNORE_JOBS,SPEC_NODES",
        "licenses": {},
        "node_cnt": 1,
        "node_list": "cn-c002",
        "partition": null,
        "start_time": 1618938656,
        "tres_str": [
            "cpu=64"
        ],
        "users": [
            "badrinaa",
            "bilaniuo",
            "mamlouka"
        ]
    }
}
```

