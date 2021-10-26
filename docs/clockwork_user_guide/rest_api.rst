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
                "cw": {}
                "raw": {},
                "processed": {}
            },
            {
                "cw": {}
                "raw": {},
                "processed": {}
            }
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
            "cw": {}
            "raw": {},
            "processed": {}
        }

   :query job_id: string containing the job_id as defined by Slurm
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 400: missing `job_id`
   :statuscode 401: bad authorization
   :statuscode 500: more than one entries were found


.. http:get:: /api/v1/cluster/jobs/user_dict_update

    [NOT IMPLEMENTED YET]
    [DEV NOTE: Is it even possible to transfer a dict with GET instead of POST?
    Try that out and see how it affects design.]

    Update the `user_dict` portion of an entry in the database.
    This can be used to build a lot of functionality on top of Clockwork
    and it does not conflict with the attributes read from Slurm.

    A user can only affect the `user_dict` on jobs that they own.
    This means that the server will validate that the user issuing
    the call, as identified by the `Authorization` header, is the owner
    of the job being described uniquely by the arguments `job_id` and
    `cluster_name`.
    
    A dict `update` argument is required and its key-values
    will be merged with the target entry from the database.

   **Example request**:

   .. sourcecode:: http

        GET /api/v1/cluster/jobs/user_dict_update
        Host: clockwork.mila.quebec
        Accept: application/json

   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "cw": {}
            "raw": {},
            "processed": {}
        }

   :query job_id: string containing the job_id as defined by Slurm
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :query update: dict with key-values to update in the database
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
            },
            {
            }
        ]

   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 401: bad authorization


.. http:get:: /api/v1/cluster/nodes/one

    Get information about one node in the database.
    This does not return more details than calls to nodes/list,
    but it makes the request lighter for the server. [TODO: Measure this claim.]

    Takes arguments `name`, `cluster_name` to identify a node uniquely.
    
    If no valid entry is found, the result is an empty dict.
    When more than one are found, this is an error.

   **Example request**:

   .. sourcecode:: http

        GET /api/v1/cluster/node/one?name=cn-a002&cluster_name=mila
        Host: clockwork.mila.quebec
        Accept: application/json

   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
        }

   :query name: string containing the node as defined on Slurm
   :query cluster_name: (optional) "mila" or any cluster name from Compute Canada
   :reqheader Authorization: bearer token to authenticate
   :statuscode 200: success
   :statuscode 401: bad authorization
   :statuscode 500: more than one entries were found