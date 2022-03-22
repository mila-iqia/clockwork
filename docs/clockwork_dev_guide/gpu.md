# GPU data

## API requests
### Overview of the requests
The Clockwork REST API proposes three requests to retrieve GPU data:

| Request | Arguments | Example | Description |
| -- | -- | -- | -- |
| /gpu/list |  | /gpu/list | List all the GPU data contained in the Clockwork database. The returned result is a list of dictionaries, which present the same format as described in the [In the `gpu` collection](#in-the-gpu-collection) section (minus the `_id` and `cw_name` fields) |
| /gpu/one | gpu_name | /gpu/one&name=rtx8000 | Returns a dictionary presenting the data of the GPU associated to the given GPU name. The format of the response is the same as presented in the [In the `gpu` collection](#in-the-gpu-collection) section (minus the `_id` and `cw_name` fields) |
| /nodes/one/gpu | node_name, cluster_name | /nodes/one/gpu?name=cn-a003 | Returns a dictionary presenting the data of the GPU associated to the node. The format of the response is the same as presented in the [In the `gpu` collection](#in-the-gpu-collection) section (minus the `_id` and `cw_name` fields) |

### The directly implied Python files
A lot of files are implied to set up the requests, the responses, the access to the database, etc. The "directly implied Python files" (a better name could be found) are the instructions specific to each of the request described in [Overview of the requests](#overview-of-the-requests). Thus, it is not intended to be an exhaustive list.

Two types of files are identified:

* **The "route" files** check the arguments given by the user, call the helper to retrieve information from the database, correlate the data and return the response.

* **The "helper" files** contact the database to retrieved the useful information.

Thus, a list of the "helper" and "route" files used by each request is presented below:
* The `/gpu/one` and the `/gpu/list` requests imply two Python files; their "route" file is [`clockwork_web/rest_routes/gpu.py`](../../clockwork_web/rest_routes/gpu.py) while their "helper" file is [`clockwork_web/core/gpu_helper.py`](../../clockwork_web/core/gpu_helper.py).

* The `/nodes/one/gpu` request implies three Python files; its "route" file is [`clockwork_web/rest_routes/nodes.py`](../../clockwork_web/rest_routes/nodes.py) while two "helper" files are used: [`clockwork_web/core/nodes_helper.py`](../../clockwork_web/core/nodes_helper.py) and [`clockwork_web/core/gpu_helper.py`](../../clockwork_web/core/gpu_helper.py).


## GPU data
### Lifecycle
The GPU data related to a node is extracted from the Slurm report and stored in the database, as part of a `node` entry, by the module [`slurm_state`](../../slurm_state). It is then manually completed by more details on the GPU, stored in the `gpu` collection of the database, by the script [`scripts/update_gpu_information.py`](../../scripts/update_gpu_information.py). It is then made available through the Clockwork REST API (see [API requests](#api-requests)).

### Formats
#### In the `node` collection
The data stored in the `node` collection is mainly retrieved from the Slurm report. It is part of a the node description, presented in [Obtaining the state of the Slurm clusters](slurm_state.md). The parts where the GPU data appear are the following:

```
{
    "slurm": {
      ...
      "features": <features>,
      "gres": <gres>,
      ...
    },
    "cw": {
      "gpu": {
          "cw_name": <cw_name>,
          "name": <gpu_name>,
          "number": <number>,
          "associated_sockets": <associated_sockets>
      }
    }
}


```
where the `<features>` and `<gres>` values are directly extracted from the respective `AvailableFeatures` and `Gres` fields of the Slurm report ; and `<cw_name>`, `<gpu_name>`, `<number>` and `<sockets_numbers>` are deduced from their parsing.

**The values `<gpu_name>`, `<number>` and `<sockets_numbers>`** are directly extracted from the field `Gres`. Thus, if this field is set to `(null)` in the Slurm nodes report, the value of `node["cw"]["gpu"]` would be `{}`. `<gres>` has the following format: `gpu:<gpu_name>:<gpu_number>` with, optionally, at the end, some information on the sockets: for instance, `(S:0)` if the GPU are associated with socket 0, or `(S:0-1)` if associated to sockets 0 and 1. Thus, the values are extracted as follows:
```
gpu:<name>:<number>(S:(<associated_sockets>))
```

**The value `<cw_name>`** is deduced from `<name>` and the content of `<features>`. By observing Slurm nodes reports from both ComputeCanada and Mila clusters, some disparities have been observed regarding the GPU V100 and P100. As these GPUs can have different amount of RAM regarding the models, the differences between them are observed as follows:

* On the ComputeCanada side, a GPU V100 presenting 32GB of RAM is called `v100l` in the `Gres` field of the Slurm report, while one presenting 16GB of RAM is simply identified as `v100`. In a similar way, a GPU P100 is referred as `p100l` if it presents 16GB of RAM, while its name is `p100` if its amount of RAM is of 12GB.

* This difference is not retrieved by the same way in the Slurm nodes reports of the Mila cluster. The GPU V100 is called `v100`, regardless if it provides 16GB or 32GB of RAM. However, the RAM information can be retrieved in the content of `<features>` (which is not the case in the ComputeCanada Slurm nodes report). This field presents the following format: `<microarchitecture_data>,...,<ram>gb`.

The value of `<cw_name>` follows the ComputeCanada convention. Thus, the amount of RAM is retrieved from `<features>` when a V100 or P100 is encountered.

To conclude, the following array sums up the contents of the fields presented above:

| Field name | Type | Example | Description |
| -- | -- | -- | -- |
| features | string | "x86_64,volta,32gb" | The content of the `AvailableFeatures` field of the Slurm nodes report |
| gres | string | "gpu:v100:8(S:0-1)" | The content of the `Gres` field of the Slurm nodes report |
| cw_name | string | "v100l" | The GPU name according to the Clockwork convention |
| gpu_name | string | "v100" | The GPU name as displayed in the Slurm report |
| number | integer | 8 | The number of GPU of this kind on the node |
| associated_sockets | string | "0-1" | The sockets associated to the GPU. For instance, "(S:0)" if the GPU are associated with socket 0, or "(S:0-1)" if associated with sockets 0 and 1. |


#### In the `gpu` collection
GPU specifications present the following format:
```
{
    "_id": <mongodb_id>
    "cw_name": <cw_gpu_name>,
    "name": <gpu_name>,
    "vendor": <gpu_vendor>,
    "ram": <ram_in_gb>,
    "cuda_cores": <cuda_cores>,
    "tensor_cores": <tensor_cores>,
    "tflops_fp32": <tflops_fp32>
}
```
where `<mongodb_id>` is generated when the entry is inserted into the `gpu` collection of the database. `<cw_gpu_name>` refers to `<cw_name>` and `<gpu_name>` to `<name>`, both presented in the section [In the `node` collection](#in-the-node-collection). Other information contained in this dictionary has been manually retrieved and stored in the database.

The following array presents a quick overview of the fields listed in this dictionary:

| Field name | Type | Example | Description |
| -- | -- | -- | -- |
| <mongodb_id> | ObjectId (type used by MongoDB) |  | An ID generated by MongoDB when the entry has been inserted in the `gpu` collection |
| <cw_gpu_name> | string | "v100l" | The GPU name according to the Clockwork convention |
| <gpu_name> | string | "v100" | The GPU name as displayed in the Slurm report |
| <gpu_vendor> | string | "nvidia" | The name of the GPU's vendor |
| <ram> | float | 32 | The number of GB of the GPU's RAM |
| <cuda_cores> | integer | 5120 | The number of CUDA cores of the GPU |
| <tensor_cores> | integer | 640 | The number of tensor cores of the GPU |
| <tflops_fp32> | float | 15.7 | The number of TFLOPS for a FP32 performance (theoretical computing power with single-precision) |
