REST API
========

TODO :  Put the contents of the query results once we nail down the format
        that we want to use for the database.

jobs
----

.. http:get:: /api/v1/cluster/jobs/list

    List all the jobs in the database.
    Takes optional arguments `user`, `time`, `cluster_name`
    to narrow down the request to avoid
    returning a large quantity of finished jobs
    or jobs belonging to other users.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/cluster/jobs/list
        Host: clockwork.mila.quebec
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "slurm": {
                    "job_id": "820432",
                    "name": "somejobname_244745",
                    "cc_account_username": "ccuser01",
                    "uid": "10001",
                    "account": "def-pomme-rrg",
                    "job_state": "PENDING",
                    "exit_code": "0:0",
                    "time_limit": 10800,
                    "submit_time": "2020-02-04T03:22:55-05:00",
                    "start_time": "Unknown",
                    "end_time": "Unknown",
                    "partition": "fun_partition",
                    "nodes": null,
                    "command": "/a762/b220/c552",
                    "work_dir": "/a751/b704/c43",
                    "stderr": "/a869/b72/c702.err",
                    "stdin": "/dev/null",
                    "stdout": "/a942/b827/c342.out",
                    "cluster_name": "beluga"},
                "cw": {
                    "cc_account_username": "ccuser01",
                    "mila_cluster_username": null,
                    "mila_email_username": null},
                "user": {}
            },
            {"slurm": {}, "cw": {}, "user": {}},
            {"slurm": {}, "cw": {}, "user": {}},
        ]

   :query user: (optional) any of the 3 kinds of usernames
   :query time: (optional) integer number of seconds for cutoff for finished jobs
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 400: invalid integer value for time
   :statuscode 401: bad authorization


.. http:get:: /api/v1/cluster/jobs/one

    List one job in the database.
    Takes arguments `job_id`, `cluster_name` to identify a job uniquely.
    The `cluster_name` is not necessary if the `job_id` is already unique
    in the database.

    If no valid entry is found, the result is an empty dict.
    When more than one are found, this is an error.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/cluster/jobs/one?job_id=233874&cluster_name=mila
        Host: clockwork.mila.quebec
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "slurm": {
                "job_id": "233874",
                "name": "somejobname_942640",
                "mila_cluster_username": "milauser12",
                "uid": "10012",
                "account": "mila",
                "job_state": "RUNNING",
                "exit_code": "0:0",
                "time_limit": 604800,
                "submit_time": "2021-11-13T00:56:47-05:00",
                "start_time": "2021-11-13T01:16:31-05:00",
                "end_time": "2021-11-20T01:16:31-05:00",
                "partition": "fun_partition",
                "nodes": "cn-b005",
                "resv_name": "transtech",
                "command": "/a58/b740/c718",
                "work_dir": "/a308/b872/c331",
                "stderr": "/a3/b765/c675.err",
                "stdin": "/dev/null",
                "stdout": "/a129/b104/c145.out",
                "cluster_name": "mila"},
            "cw": {
                "cc_account_username": null,
                "mila_cluster_username": "milauser12",
                "mila_email_username": null},
            "user": {}
        }

    :query job_id: string containing the job_id as defined by Slurm
    :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
    :reqheader Authorization: bearer token to authenticate
    :statuscode 200: success
    :statuscode 400: missing `job_id`
    :statuscode 401: bad authorization
    :statuscode 500: more than one entries were found


.. http:put:: /api/v1/cluster/jobs/user_dict_update

    Update the "user" portion of a job entry in the database.
    This can be used to build a lot of functionality on top of Clockwork
    and it does not conflict with the attributes read from Slurm.

    A user can only affect the "user" dict on jobs that they own.
    This means that the server will validate that the user issuing
    the call, as identified by the `Authorization` header, is the owner
    of the job being described uniquely by the arguments `job_id` and
    `cluster_name`.

    A dict `update_pairs` argument is required and its key-values
    will be merged with the target entry from the database.

    On a succesful call, the value returned is the new updated
    user dict (not the complete job entry).

   **Example request**:

   .. sourcecode:: http

        PUT /api/v1/cluster/jobs/user_dict_update
        Host: clockwork.mila.quebec
        Accept: application/json

   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "train_loss": 0.20,
            "valid_loss": 0.30,
            "nbr_dinosaurs": 10
        }

   :query job_id: string containing the job_id as defined by Slurm
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :query update_pairs: dict with key-values to update in the database
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 400: missing `job_id`
   :statuscode 401: bad authorization
   :statuscode 500: more than one entries were found


nodes
-----


.. http:get:: /api/v1/cluster/nodes/list

    List all the cluster nodes in the database.
    Takes optional argument `cluster_name`.
    Contrary to the information on jobs,
    most of the information on nodes tends to stay
    constant.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/cluster/nodes/list?cluster_name=beluga
        Host: clockwork.mila.quebec
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "slurm": {
                    "name": "blg4118",
                    "arch": "x86_64",
                    "features": "skylake",
                    "gres": null,
                    "addr": "blg4118",
                    "memory": "191000",
                    "state": "ALLOCATED",
                    "cfg_tres": "cpu=40,mem=191000M,billing=46",
                    "alloc_tres": "cpu=40,mem=160000M",
                    "cluster_name": "beluga"},
                "cw": {}
            },
            {"slurm": {}, "cw": {}},
            {"slurm": {}, "cw": {}},
        ]

   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 401: bad authorization

.. http:get:: /api/v1/cluster/nodes/one
    Get information about one node in the database.
    This does not return more details than calls to nodes/list,
    but it makes the request lighter for the server. [TODO: Measure this claim.]

    Takes arguments `node_name`, `cluster_name` to identify a node uniquely.

    If no valid entry is found, the result is an empty dict.
    When more than one are found, this is an error.

    **Example request**:

    .. sourcecode:: http

         GET /api/v1/cluster/nodes/one?name=cn-a002&cluster_name=mila
         Host: clockwork.mila.quebec
         Accept: application/json

    **Example response**:

    .. sourcecode:: http

         HTTP/1.1 200 OK
         Content-Type: application/json

         {
             "slurm": {
                 "name": "cn-a002",
                 "arch": "x86_64",
                 "features": "broadwell",
                 "gres": null,
                 "addr": "cn-a002",
                 "memory": "128000",
                 "state": "ALLOCATED",
                 "cfg_tres": "cpu=32,mem=125G,billing=32",
                 "alloc_tres": "cpu=32,mem=122528M",
                 "comment": null,
                 "cluster_name": "mila"},
             "cw": {}
         }

    :query name: string containing the node name as defined on Slurm
    :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
    :reqheader Authorization: bearer token to authenticate
    :statuscode 200: success
    :statuscode 401: bad authorization
    :statuscode 500: more than one entries were found


.. http:get:: /api/v1/cluster/nodes/one/gpu

    Describe the GPU of a node.

    Take one mandatory `name`.
    This could also take a `cluster_name` argument if we have two clusters that
    have clashes with their host names.

    If no valid entry is found, the result is an empty dict.

   **Example request**:

   .. sourcecode:: http

        GET /api/v1/cluster/node/one?node_name=cn-a002&cluster_name=mila
        Host: clockwork.mila.quebec
        Accept: application/json

   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
              "name": rtx8000,
              "vendor": nvidia,
              "ram": 48,
              "cuda_cores": 4608,
              "tensor_cores": 576,
              "tflops_fp32": 16.3
        }

   **Details of a response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
              "name": <gpu_name>,
              "vendor": <gpu_vendor>,
              "ram": <ram_in_gb>,
              "cuda_cores": <cuda_cores>,
              "tensor_cores": <tensor_cores>,
              "tflops_fp32": <tflops_fp32>
        }
        with:
            - <gpu_name> a string presenting the GPU name as described in the Slurm report
            - <gpu_vendor> a string containing the name of the GPU's vendor
            - <ram_in_gb> a float which is the number of GB of the GPU's RAM
            - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
            - <tensor_cores> an integer presenting the number of tensor cores of the GPU
            - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
              (theoretical computing power with single-precision)

   :query name: string containing the node name as defined on Slurm
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 400: bad request (missing argument `name`)
   :statuscode 401: bad authorization


gpu
---

.. http:get:: /api/v1/cluster/gpu/one

    Get the specifications of one GPU in the database.

    This does not return more details than calls to gpu/list,
    but it makes the request lighter for the server. [TODO: Measure this claim.]

    Take one mandatory `gpu_name` to identify a GPU uniquely. The `gpu_name` is
    used to identify the GPU in the Clockwork database. Thus, it is based on
    the `cw_name` of the GPU, and not its `name` argument.

    If no valid entry is found, the result is an empty dict.

    **Example request**:

    .. sourcecode:: http

         GET /api/v1/cluster/gpu/one?gpu_name=rtx8000
         Host: clockwork.mila.quebec
         Accept: application/json

    **Example response**:

    .. sourcecode:: http

         HTTP/1.1 200 OK
         Content-Type: application/json

         {
               "name": rtx8000,
               "vendor": nvidia,
               "ram": 48,
               "cuda_cores": 4608,
               "tensor_cores": 576,
               "tflops_fp32": 16.3
         }

    **Details of a response**:

    .. sourcecode:: http

         HTTP/1.1 200 OK
         Content-Type: application/json

         {
               "name": <gpu_name>,
               "vendor": <gpu_vendor>,
               "ram": <ram_in_gb>,
               "cuda_cores": <cuda_cores>,
               "tensor_cores": <tensor_cores>,
               "tflops_fp32": <tflops_fp32>
         }
         with:
             - <gpu_name> a string presenting the GPU name as described in the Slurm report
             - <gpu_vendor> a string containing the name of the GPU's vendor
             - <ram_in_gb> a float which is the number of GB of the GPU's RAM
             - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
             - <tensor_cores> an integer presenting the number of tensor cores of the GPU
             - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
               (theoretical computing power with single-precision)


    :query gpu_name: string containing the GPU name, as defined on Clockwork
    :reqheader Authorization: bearer token to authenticate
    :statuscode 200: success
    :statuscode 400: bad request (missing argument)
    :statuscode 401: bad authorization


.. http:get:: /api/v1/cluster/gpu/list

    List the GPU specifications stored in the database.

    Take no argument.

    Can return an empty list.

    **Example request**:

    .. sourcecode:: http

         GET /api/v1/cluster/gpu/list
         Host: clockwork.mila.quebec
         Accept: application/json

    **Example response**:

    .. sourcecode:: http

         HTTP/1.1 200 OK
         Content-Type: application/json

         [
           {
                 "name": rtx8000,
                 "vendor": nvidia,
                 "ram": 48,
                 "cuda_cores": 4608,
                 "tensor_cores": 576,
                 "tflops_fp32": 16.3
           },
           {
                 "cw_name": "v100",
                 "name": "v100",
                 "vendor": "nvidia",
                 "ram": 16,
                 "cuda_cores": 5120,
                 "tensor_cores": 640,
                 "tflops_fp32": 15.7
           }
         ]

    **Details of a response**:

    .. sourcecode:: http

         HTTP/1.1 200 OK
         Content-Type: application/json

         Return a list of the specifications stored in the database. This is a list
         of dictionaries describing each one a GPU. Such a dictionary presents the
         following format:
         {
             "name": <gpu_name>,
             "vendor": <gpu_vendor>,
             "ram": <ram_in_gb>,
             "cuda_cores": <cuda_cores>,
             "tensor_cores": <tensor_cores>,
             "tflops_fp32": <tflops_fp32>
         }
         with:
             - <gpu_name> a string presenting the GPU name as described in the Slurm report
             - <gpu_vendor> a string containing the name of the GPU's vendor
             - <ram_in_gb> a float which is the number of GB of the GPU's RAM
             - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
             - <tensor_cores> an integer presenting the number of tensor cores of the GPU
             - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
               (theoretical computing power with single-precision)


    :reqheader Authorization: bearer token to authenticate
    :statuscode 200: success
    :statuscode 401: bad authorization
