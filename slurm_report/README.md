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
The content of this folder is used to generate realist tests data, contained in the file `test_common/fake_data.json`. The script
`clockwork/produce_fake_data.sh` presents the following steps:
1. Generate fake users
2. Anonymize the data contained in the `scontrol_show_job` and `scontrol_show_job`
files for each cluster (namely by using the fake users)
3. Store the data in a JSON file (and may add it to the database, if requested)
4. Concatenate the JSON files corresponding to the users, nodes, jobs and gpus
into the `clockwork/test_common/fake_data.json`.

### The clusters
As a sanity measure for now, we restrict the "cluster" folders (i.e. `cluster1`, ..., `clusterN`) to be from the list of clusters that we currently have access to. That is, `beluga`, `cedar`, `graham`, `mila`, `narval`.

### Temporary files generated while producing the fake data
During the process of test data generation, several files are created directly in `slurm_report`:

| File | Created during step |  Description |
| -- | -- | -- |
| `fake_users.json` | 1. Fake users generation | This file contains fake users in order to keep a realistic relation between some jobs with each other without having information related to real users |
| `subset_100_jobs_anonymized.json` | 4. Concatenate the JSON files | This is a temporary file created by the script `concat_json_lists.py`. It contains the list of anonymized jobs, which will be "stitched" in the `fake_data.json` dictionary as the value corresponding to the key `jobs`. |
| `subset_100_nodes_anonymized.json` | 4. Concatenate the JSON files | This is a temporary file created by the script `concat_json_lists.py`. It contains the list of anonymized nodes, which will be "stitched" in the `fake_data.json` dictionary as the value corresponding to the key `nodes`. |

Other files are generated for each cluster folder:

| File | Created during step |  Description |
| -- | -- | -- |
| `job_anonymized_dump_file.json` | 3. Store the data in a JSON file | This file, generated by the script `slurm_state.read_report_commit_to_db`, is a JSON list representing an anonymized subset of this cluster's jobs. It is the JSON translation of the file `scontrol_show_job_anonymized`. |
| `node_anonymized_dump_file.json` | 3. Store the data in a JSON file | This file, generated by the script `slurm_state.read_report_commit_to_db`, is a JSON list representing an anonymized subset of this cluster's nodes. It is the JSON translation of the file `scontrol_show_node_anonymized`. |
| `scontrol_show_job_anonymized` | 2. Anonymize the data | This file presents the same format as `scontrol_show_job`, but the data have been anonymized by the script `slurm_state.anonymize_scontrol_report`, and only a subset of them has been kept.  |
| `scontrol_show_node_anonymized` | 2. Anonymize the data | This file presents the same format as `scontrol_show_node`, but the data have been anonymized by the script `slurm_state.anonymize_scontrol_report`, and only a subset of them has been kept. |

## Formats
For more details on the resulting formats, please see the "Slurm state" section of the Developer guide.