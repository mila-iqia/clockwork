# Slurm report folder
## Global
This folder is used to store the data retrieved through Slurm commands
`scontrol show job` and `scontrol show node` on the different clusters.
Its expected structure is the following:

```
.
└── slurm_report
    ├── cluster1
    │   ├── scontrol_show_job # Stores the data retrieved by `scontrol show job` on the cluster `cluster1`
    │   └── scontrol_show_node # Stores the data retrieved by `scontrol show node` on the cluster `cluster1`
    ├── cluster2
    │   ├── scontrol_show_job
    │   └── scontrol_show_node
    ├── ...
    └── clusterN
        ├── scontrol_show_job
        └── scontrol_show_node
```

## Usage
The content of this folder is used to generate realist tests data. The script
`clockwork/produce_fake_data.sh` presents the following steps:
1. Generate fake users
2. Anonymize the data contained in the `scontrol_show_job` and `scontrol_show_job`
files for each cluster (namely by using the fake users)
3. Store the data in a JSON file (and may add it to the database, if requested)
4. Concatenate the JSON files corresponding to the users, nodes, jobs and gpus
into the `clockwork/test_common/fake_data.json`.

### The clusters
To be taken into account, the different "cluster folders" (introduced as `cluster1`,
`cluster2`, and `cluterN`) must be called using existing cluster names (thus,
each name has to be contained in the following list:
* beluga
* cedar
* graham
* mila
* narval

### Temporary files generated while producing the fake data
During the process of test data generation, several files are created directly in `slurm_report`:

| File | Created during step |  Description |
| -- | -- | -- |
| `fake_users.json` | 1. Fake users generation |  |
| `generate_clusterstats_cache.sh` |  |  |
| `subset_100_jobs_anonymized.json` |  |  |
| `subset_100_nodes_anonymized.json` |  |  |

Other files are generated for each cluster folder:

| File | Created during step |  Description |
| -- | -- | -- |
| `job_anonymized_dump_file.json` |  |  |
| `node_anonymized_dump_file.json` |  |  |
| `scontrol_show_job_anonymized` |  |  |
| `scontrol_show_node_anonymized` |  |  |
