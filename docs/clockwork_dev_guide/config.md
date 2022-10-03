# Configuration

[TODO]

## Clusters configuration
A new cluster is added to the `.toml` configuration file by writing a paragraph such as follows in this file:

```
[clusters.narval]
account_field="cc_account_username"
update_field="cc_account_update_key"
allocations=["def-patate-rrg", "def-pomme-rrg", "def-cerise-rrg", "def-citron-rrg"]
timezone="America/Montreal"
organization="Digital Research Alliance of Canada"
nbr_cpus=2608
nbr_gpus=636
official_documentation="https://docs.alliancecan.ca/wiki/Narval"
display_order=4
```

The previous example depicts a test configuration of the "narval" cluster.

The cluster is first defined by its name as follows:

```
[clusters.<cluster_name>]
```

Further details can be then added by adding one line of the following format per parameters:

```
<parameters_key>: <parameter_value>
```

Here is a list of the possible parameters for a cluster:

| Parameter | Mandatory/Optional | Description |
| -- | -- | -- |
| account_field | Mandatory | The key under which the cluster's users' identifier are stored by Clockwork |
| update_field | Optional |  |
| allocations | Mandatory (Either "*" or a list of strings) | The names of this cluster's allocations. |
| timezone | Mandatory | The timezone on which the servers of the cluster are. |
| organization | Optional (default value: False) | The name of the organization in charge of the cluster. |
| nbr_cpus | Optional (default: 0) | The number of CPUs this cluster contains. |
| nbr_gpus | Optional (default: 0) | The number of GPUs this cluster contains. |
| official_documentation | Optional (default: False) | Link to the official documentation of the cluster. |
| mila_documentation | Optional (default: False) | Link to the Mila documentation of the cluster. |
| display_order | Optional (default value: 9999) | Integer used to define the order in which the clusters are displayed. The lower the display order indice is, the higher in the list the cluster will be. |