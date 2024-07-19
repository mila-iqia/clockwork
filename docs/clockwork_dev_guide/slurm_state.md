# Obtaining the state of the Slurm clusters

## Supported clusters

We gather the Slurm data from 4 clusters at the current time.

| cluster_name | jurisdiction   | URL |
|--------------|----------------|-----|
| mila         | Mila           | docs.mila.quebec |
| beluga       | Compute Canada | [https://docs.computecanada.ca/wiki/B%C3%A9luga/en](https://docs.computecanada.ca/wiki/B%C3%A9luga/en) |
| cedar        | Compute Canada | [https://docs.computecanada.ca/wiki/Cedar/en](https://docs.computecanada.ca/wiki/Cedar/en) |
| graham       | Compute Canada | [https://docs.computecanada.ca/wiki/Graham/en](https://docs.computecanada.ca/wiki/Graham/en)|

Compute Canada generates reports automatically every 10 minutes
and we simply rsync the results over to the machine where our
database is running. We do the same thing on the Mila cluster,
except we also have to run the report scripts for ourselves.

More information is found in the following readme file :
[slurm_state/cron_scripts/readme.md](https://github.com/mila-iqia/clockwork/tree/master/slurm_state/cron_scripts)

## Data formats

To see an example of the data stored in the database,
we can refer to
[test_common/fake_data.json](https://github.com/mila-iqia/clockwork/tree/master/test_common/fake_data.json)
which contains fake data for the unit tests.

Job and node entries both contain a "slurm" component based
on the data that we read from Slurm.
They also contain a "cw" component that Clockwork uses
to store extra information.

### Jobs format

Jobs are stored in the database in the following format:
```json
{
    "slurm": {
        "job_id": "4553",
        "name": "somejobname_779002",
        "cc_account_username": "ccuser02",
        "uid": "10002",
        "account": "def-patate-rrg",
        "job_state": "RUNNING",
        "exit_code": "0:0",
        "time_limit": 864000,
        "submit_time": "2021-08-25T15:36:16-04:00",
        "start_time": "2021-11-14T11:17:18-05:00",
        "end_time": "2021-11-24T11:17:18-05:00",
        "partition": "fun_partition",
        "nodes": "gra12",
        "command": "/a481/b60/c644",
        "work_dir": "/a534/b490/c888",
        "stderr": "/a118/b218/c447.err",
        "stdin": "/dev/null",
        "stdout": "/a884/b115/c947.out",
        "cluster_name": "graham"
    },
    "cw": {
        "cc_account_username": "ccuser02",
        "mila_cluster_username": null,
        "mila_email_username": null
    }
}
```

### Nodes format

Nodes are stored in the database in the following format:

```json
{
    "slurm": {
    "name": "ced0061",
    "arch": "x86_64",
    "features": "broadwell",
    "gres": "gpu:gpuname:8(S:0-1)",
    "addr": "ced0061",
    "memory": "128000",
    "state": "ALLOCATED",
    "cfg_tres": "cpu=32,mem=125G,billing=32",
    "alloc_tres": "cpu=32,mem=122528M",
    "comment": null,
    "cluster_name": "cedar"
    },
    "cw": {
      "gpu": {
              "cw_name": "cwgpuname",
              "name": "gpuname",
              "number": 8,
              "associated_sockets": "0-1"
          }
    }
},
```

### Private information?

Note that, in all cases, all the information in the database
is accessible to everyone in the same way that it is accessible
by all users on the original Slurm clusters. Anyone can list
all the jobs running on the clusters.

This is different from information being public on the Internet
since the requirements for using the Slurm clusters are basically
the same as the requirements for accessing those clusters.
Users are asked in the same way to refrain from sharing publicly
the information from Clockwork just like they should refrain
from doing so with the information on the Mila cluster or
on the Compute Canada cluster.

## Some MongoSH commands

When you want to wipe out the contents of a collection (e.g. "jobs")
but not remove an associated "index" that has been configured,
you can use the MongoSH terminal inside MongoDB Compass.
```
use clockwork
db.jobs.deleteMany({})
```
