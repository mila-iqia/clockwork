from __future__ import annotations
import requests
import base64
import json
import os


class ClockworkToolsBaseClient:
    """
    Implements the client to a "Clockwork" web server already running.
    This class is not meant to be used directly by users because we generally
    want to direct them towards the other class ClockworkToolsClient featuring
    some additional default values and flexibility.
    """

    def __init__(
        self,
        email: str,
        clockwork_api_key: str,
        host: str = "clockwork.mila.quebec",
        port: int = 443,
    ):
        """Constructor for the ClockworkToolsBaseClient client.

        Args:
            config (dict): Configuration for the client.
            Contains keys 'host', 'port', 'email', 'clockwork_api_key'.
            Eventually the 'host' and 'port' will have default values
            that refer to our service in production.
        """

        self.email = email
        self.clockwork_api_key = clockwork_api_key
        self.host = host
        self.port = port

        # When deployed for real, we might want to be a little more careful
        # to protect people against sending http by accident to remote hosts.
        # Not sure what the correct thing to do would be.
        if self.port == 443:
            http_or_https = "https"
        else:
            http_or_https = "http"

        self.complete_base_address = f"{http_or_https}://{self.host}:{self.port}"

    def _get_headers(self):
        """Get headers of REST API calls. Includes authentication.

        Returns:
            dict: The headers to be used. Includes authentication.
        """
        # This is a common way to identify http requests.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization
        #
        # Note that the headers are hidden by TLS when using HTTPS
        # so they are not visible in transit.
        s = f"{self.email}:{self.clockwork_api_key}"
        encoded_bytes = base64.b64encode(s.encode("utf-8"))
        encoded_s = str(encoded_bytes, "utf-8")
        return {"Authorization": f"Basic {encoded_s}"}

    def _request(self, endpoint, params, method="GET", send_json=True):
        """Helper method for REST API calls.

        Internal helper method to make the calls to the REST API endpoints
        for many different methods of `self`. Hidden from the user.

        Args:
            endpoint (str): The REST endpoint, omitting the server address.
            params (dict): Arguments to be provided to the REST endpoint.
            send_json (bool): Optional. If True and if method is PUT,
                then request will be sent as a JSON request.


        Returns:
            Depends on the call made.
        """
        if endpoint.startswith("/") or self.complete_base_address.endswith("/"):
            middle_slash = ""
        else:
            middle_slash = "/"

        assert method in ["GET", "PUT"]

        complete_address = f"{self.complete_base_address}{middle_slash}{endpoint}"
        if method == "GET":
            response = requests.get(
                complete_address, params=params, headers=self._get_headers()
            )
        elif method == "PUT":
            if send_json:
                headers = self._get_headers()
                headers["Content-type"] = "application/json"
                response = requests.put(complete_address, json=params, headers=headers)
            else:
                response = requests.put(
                    complete_address, data=params, headers=self._get_headers()
                )

        # Check code instead and raise exception if it's the wrong one.
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Server rejected call with code {response.status_code}. {response.json()}"
            )

    # For endpoints requiring `params` we could use **kwargs instead,
    # but let's use explicit arguments instead.
    def jobs_list(
        self, username=None, relative_time=None, cluster_name: str = None
    ) -> list[dict[str, any]]:
        """REST call to api/v1/clusters/jobs/list.

        Gets a list with detailed description of a all the jobs
        from the specified cluster.

        Args:
            username (str): Name of user.
            relative_time (int): How many seconds to go back in time to list jobs.
            cluster_name (str): Name of cluster.

        Returns:
            list[dict[str,any]]: List of properties of all the jobs.
            If cluster_name is invalid, returns an empty list.
        """
        endpoint = "api/v1/clusters/jobs/list"
        params = {}
        for (k, a) in [
            ("username", username),
            ("relative_time", relative_time),
            ("cluster_name", cluster_name),
        ]:
            if a is not None:
                params[k] = a
        return self._request(endpoint, params)

    def jobs_one(self, job_id: str = None, cluster_name: str = None) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/one.

        Gets the detailed description of a single job
        on the cluster specified. If there is no ambiguity
        with the job_id, the cluster_name argument
        is not required.

        Args:
            job_id (str): job_id to be described (in terms of Slurm terminology)
            cluster_name (str): Name of cluster where that job is running.

        Returns:
            dict[str,any]: Properties of the job, when valid.
            Otherwise returns an empty dict.
        """
        endpoint = "api/v1/clusters/jobs/one"
        params = {}
        for (k, a) in [
            ("job_id", job_id),
            ("cluster_name", cluster_name),
        ]:
            if a is not None:
                params[k] = a
        return self._request(endpoint, params)

    def get_user_props(self, job_id: str, cluster_name: str) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/user_props/get.

        Call for get_user_props().

        Args:
            job_id (str): ID of job to retrieve props
            cluster_name (str): Name of job cluster

        Returns:
            dict[any,any]: props.
        """
        endpoint = "api/v1/clusters/jobs/user_props/get"
        params = {"job_id": job_id, "cluster_name": cluster_name}
        return self._request(endpoint, params)

    def set_user_props(
        self, job_id: str, cluster_name: str, updates: dict
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/user_props/set.

        Call for set_user_props().

        Args:
            job_id (str): ID of job to retrieve props
            cluster_name (str): Name of job cluster
            updates (dict): Dict of props to update.

        Returns:
            dict[any,any]: Returns the updated props.
        """
        endpoint = "api/v1/clusters/jobs/user_props/set"
        params = {"job_id": job_id, "cluster_name": cluster_name, "updates": updates}
        return self._request(endpoint, params, method="PUT")

    def delete_user_props(
        self, job_id: str, cluster_name: str, keys: str | list
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/user_props/delete.

        Call for delete_user_props().

        Args:
            job_id (str): ID of job to retrieve props
            cluster_name (str): Name of job cluster
            keys (list): List of keys to delete.

        Returns:
            dict[any,any]: Returns the updated props.
        """
        endpoint = "api/v1/clusters/jobs/user_props/delete"
        params = {"job_id": job_id, "cluster_name": cluster_name, "keys": keys}
        return self._request(endpoint, params, method="PUT")

    def jobs_user_dict_update(
        self, job_id: str = None, cluster_name: str = None, update_pairs: dict = {}
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/user_dict_update.

        Updates the "user" component of a job that belongs to
        the user calling this function. Allows for any number
        of fields to be set.

        If there is no ambiguity with the job_id,
        the cluster_name argument is not required.

        Fails when the job does not belong to the user,
        or when the job is not yet in the database
        (such as during delays between the creation of the job
        and its presence in the database).

        Args:
            job_id (str): job_id to be described (in terms of Slurm terminology)
            cluster_name (str): Name of cluster where that job is running.
            update_pairs (dict): Updates to perform to the user dict.

        Returns:
            dict[any,any]: Returns the updated user dict.
        """
        endpoint = "api/v1/clusters/jobs/user_dict_update"
        params = {}

        for (k, a) in [
            ("job_id", job_id),
            ("cluster_name", cluster_name),
        ]:
            if a is not None:
                params[k] = a
        # Due to current constraints, we have to pass "update_pairs"
        # as a string representing a structure in json.
        params["update_pairs"] = json.dumps(update_pairs)
        return self._request(endpoint, params, method="PUT", send_json=False)

    def nodes_list(self, cluster_name: str = None) -> list[dict[str, any]]:
        """REST call to api/v1/clusters/nodes/list.

        Gets a list with detailed description of a all the nodes
        from the specified cluster.

        Args:
            cluster_name (str): Name of cluster.

        Returns:
            list[dict[str,any]]: List of properties of all the nodes.
            If cluster_name is invalid, returns an empty list.
        """
        endpoint = "api/v1/clusters/nodes/list"
        params = {}
        for (k, a) in [
            ("cluster_name", cluster_name),
        ]:
            if a is not None:
                params[k] = a
        return self._request(endpoint, params)

    def nodes_one(
        self, node_name: str = None, cluster_name: str = None
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/nodes/one.

        Gets the detailed description of a single node
        on the cluster specified. If there is no ambiguity
        with the node_name of the node, the cluster_name argument
        is not required.

        Args:
            node_name (str): Name of node to be described.
            cluster_name (str): Name of cluster where that node lives.

        Returns:
            dict[str,any]: Properties of the node, when valid.
            Otherwise returns an empty dict.
        """
        endpoint = "api/v1/clusters/nodes/one"
        params = {}
        for (k, a) in [
            ("node_name", node_name),
            ("cluster_name", cluster_name),
        ]:
            if a is not None:
                params[k] = a
        return self._request(endpoint, params)


class ClockworkToolsClient(ClockworkToolsBaseClient):
    """
    Implements the client to a "Clockwork" web server already running.
    This simplifies the interface for Mila members in some ways,
    mainly in hiding all the decisions about the REST API and the fact
    that authenticated happens through headers.

    We can also use that client's interface to smoothe certain rough edges
    that might come up later as this "Clockwork" project unfolds.
    """

    def __init__(
        self,
        email: str = "",
        clockwork_api_key: str = "",
        host: str = "clockwork.mila.quebec",
        port: int = 443,
    ):
        """Constructor for the ClockworkTools client.

        Args:
            email (str): email to identify the user as defined by LDAP,
                         in the form username@domain (optional)
                         Read as shell environment variable is missing.
            clockwork_api_key (str): special key to identify the user as defined
                         on the clockwork web service (optional)
                         Read as shell environment variable is missing.
            host (str): URI for the clockwork web service (optional)
            port (int): port for the clockwork web service (optional)
        """

        # If we have values supplied, then use those values for the parent class.
        # Otherwise, try to read them from the environment. Nothing in Clockwork
        # can work without some form of authentication, so we insist on finding
        # those values somewhere.
        if not clockwork_api_key:
            if "CLOCKWORK_API_KEY" in os.environ and os.environ["CLOCKWORK_API_KEY"]:
                clockwork_api_key = os.environ["CLOCKWORK_API_KEY"]
            else:
                raise Exception(
                    f"Invalid clockwork_api_key argument or missing from environment."
                )

        if not email:
            if "CLOCKWORK_EMAIL" in os.environ and os.environ["CLOCKWORK_EMAIL"]:
                email = os.environ["CLOCKWORK_EMAIL"]
            else:
                raise Exception(f"Invalid email argument or missing from environment.")

        super().__init__(
            email=email,
            clockwork_api_key=clockwork_api_key,
            host=host,
            port=port,
        )

        # Additional feature on top of the parent class.
        # We will store default values that can be used to avoid
        # specifying all the arguments in situations in which
        # this python module in being used from inside a Slurm job
        # that's currently running on some particular cluster.
        self.this_specific_slurm_job_params = {}
        self._read_slurm_values_if_applicable()

    def _create_params_for_request(self, target_self: bool, **kwargs):
        """
        Special helper function to mitigate code duplication when
        preparing arguments to pass to a request in the parent class.
        """
        params = {}
        for (k, a) in kwargs.items():
            if a is not None:
                params[k] = a
            elif target_self and k in self.this_specific_slurm_job_params:
                params[k] = self.this_specific_slurm_job_params[k]
        return params

    # For endpoints requiring `params` we could use **kwargs instead,
    # but let's use explicit arguments instead.
    def jobs_list(
        self, username=None, relative_time=None, cluster_name: str = None
    ) -> list[dict[str, any]]:
        """REST call to api/v1/clusters/jobs/list.

        Gets a list with detailed description of a all the jobs
        from the specified cluster.

        Args:
            username (str): Name of user.
            relative_time (int): How many seconds to go back in time to list jobs.
            cluster_name (str): Name of cluster.

        Returns:
            list[dict[str,any]]: List of properties of all the jobs.
            If cluster_name is invalid, returns an empty list.
        """
        params = self._create_params_for_request(
            target_self=False,  # `target_self` not applicable here
            username=username,
            relative_time=relative_time,
            cluster_name=cluster_name,
        )
        return super().jobs_list(**params)

    def jobs_one(
        self, job_id: str = None, cluster_name: str = None, target_self: bool = True
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/one.

        Gets the detailed description of a single job
        on the cluster specified. If there is no ambiguity
        with the job_id, the cluster_name argument
        is not required.

        Args:
            job_id (str): job_id to be described (in terms of Slurm terminology)
            cluster_name (str): Name of cluster where that job is running.
            target_self (bool): Inside a Slurm job, automatically infer arguments
                                to target this specific Slurm job.

        Returns:
            dict[str,any]: Properties of the job, when valid.
            Otherwise returns an empty dict.
        """
        params = self._create_params_for_request(
            target_self=target_self, job_id=job_id, cluster_name=cluster_name
        )
        return super().jobs_one(**params)

    def jobs_user_dict_update(
        self,
        job_id: str = None,
        cluster_name: str = None,
        update_pairs: dict = {},
        target_self: bool = True,
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/jobs/user_dict_update.

        Updates the "user" component of a job that belongs to
        the user calling this function. Allows for any number
        of fields to be set.

        If there is no ambiguity with the job_id,
        the cluster_name argument is not required.

        Fails when the job does not belong to the user,
        or when the job is not yet in the database
        (such as during delays between the creation of the job
        and its presence in the database).

        Args:
            job_id (str): job_id to be described (in terms of Slurm terminology)
            cluster_name (str): Name of cluster where that job is running.
            update_pairs (dict): Updates to perform to the user dict.
            target_self (bool): Inside a Slurm job, automatically infer arguments
                                to target this specific Slurm job.

        Returns:
            dict[any,any]: Returns the updated user dict.
        """
        params = self._create_params_for_request(
            target_self=target_self, job_id=job_id, cluster_name=cluster_name
        )
        # Due to current constraints, we have to pass "update_pairs"
        # as a string representing a structure in json.
        # However, since the base class does the json.dump, we don't
        # want to do it twice. We therefore have to show some restraint.
        # params["update_pairs"] = json.dumps(update_pairs)  # NOT THAT
        params["update_pairs"] = update_pairs
        return super().jobs_user_dict_update(**params)

    def nodes_list(self, cluster_name: str = None) -> list[dict[str, any]]:
        """REST call to api/v1/clusters/nodes/list.

        Gets a list with detailed description of a all the nodes
        from the specified cluster.

        Args:
            cluster_name (str): Name of cluster.

        Returns:
            list[dict[str,any]]: List of properties of all the nodes.
            If cluster_name is invalid, returns an empty list.
        """
        params = self._create_params_for_request(
            target_self=False,  # `target_self` not applicable here
            cluster_name=cluster_name,
        )
        return super().nodes_list(**params)

    def nodes_one(
        self, node_name: str = None, cluster_name: str = None, target_self: bool = True
    ) -> dict[str, any]:
        """REST call to api/v1/clusters/nodes/one.

        Gets the detailed description of a single node
        on the cluster specified. If there is no ambiguity
        with the node_name of the node, the cluster_name argument
        is not required.

        Args:
            node_name (str): Name of node to be described.
            cluster_name (str): Name of cluster where that node lives.
            target_self (bool): Inside a Slurm job, automatically infer arguments
                                to target this specific Slurm job.

        Returns:
            dict[str,any]: Properties of the node, when valid.
            Otherwise returns an empty dict.
        """
        params = self._create_params_for_request(
            target_self=target_self, node_name=node_name, cluster_name=cluster_name
        )
        return super().nodes_one(**params)

    def _read_slurm_values_if_applicable(self):
        """
        When using Clockwork Tools inside a Slurm job,
        we can retrieve certain values to serve as default
        values for arguments such as "cluster_name".
        Calling for "jobs_one" can now be done without
        any argument specified and we will get the current job.

        We populate the `this_specific_slurm_job_params` member of the parent class
        as well as the `D_node` (that one is not being used outside of this function at the moment).
        """

        self.this_specific_slurm_job_params["job_id"] = os.environ.get(
            "SLURM_JOBID", None
        )

        # If we are indeed inside a slurm job, we'll proceed further and analyse
        # the node name and get its information. Otherwise, we want to avoid all that.
        if self.this_specific_slurm_job_params["job_id"]:
            # unclear yet why we want that tmpdir
            self.this_specific_slurm_job_params["job_tmpdir"] = os.environ.get(
                "SLURM_TMPDIR", None
            )

            node_name = os.uname().nodename.split(".")[0]
            self.this_specific_slurm_job_params["node_name"] = node_name
            self.D_node = self.nodes_one(node_name=node_name)

            self.this_specific_slurm_job_params["cluster_name"] = (
                self.D_node["slurm"]["cluster_name"] if self.D_node else None
            )
