from __future__ import annotations
import requests
import base64
import json


class ClockworkTools:
    """
    Implements the client to a "Clockwork" web server already running.
    This simplifies the interface for Mila members in some ways,
    mainly in hiding all the decisions about the REST API and the fact
    that authenticated happens through headers.

    We can also use that client's interface to smoothe certain rough edges
    that might come up later as this "Clockwork" project unfolds.
    """

    def __init__(self, config):
        """Constructor for the ClockworkTools client.

        Args:
            config (dict): Configuration for the client.
            Contains keys 'host', 'port', 'email', 'clockwork_api_key'.
            Eventually the 'host' and 'port' will have default values
            that refer to our service in production.
        """
        self.config = config

        # TODO : When deployed for real, we might want to be a little more careful
        #        to protect people against sending http by accident to remote hosts.
        #        Not sure what the correct thing to do would be.
        if self.config["port"] == 443:
            http_or_https = "https"
        else:
            http_or_https = "http"

        self.complete_base_address = (
            f"{http_or_https}://{self.config['host']}:{self.config['port']}"
        )

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
        s = f"{self.config['email']}:{self.config['clockwork_api_key']}"
        encoded_bytes = base64.b64encode(s.encode("utf-8"))
        encoded_s = str(encoded_bytes, "utf-8")
        return {"Authorization": f"Basic {encoded_s}"}

    def _request(self, endpoint, params, method="GET"):
        """Helper method for REST API calls.

        Internal helper method to make the calls to the REST API endpoints
        for many different methods of `self`. Hidden from the user.

        Args:
            endpoint (str): The REST endpoint, omitting the server address.
            params (dict): Arguments to be provided to the REST endpoint.

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
            response = requests.put(
                complete_address, data=params, headers=self._get_headers()
            )
        print(response)
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
        self, user=None, relative_time=None, cluster_name: str = None
    ) -> list[dict[str, any]]:
        """REST call to api/v1/clusters/jobs/list.

        Gets a list with detailed description of a all the jobs
        from the specified cluster.

        Args:
            user (str): Name of user. Matches any of the three possible kinds of usernames.
            relative_time (int): How many seconds to go back in time to list jobs.
            cluster_name (str): Name of cluster.

        Returns:
            list[dict[str,any]]: List of properties of all the jobs.
            If cluster_name is invalid, returns an empty list.
        """
        endpoint = "api/v1/clusters/jobs/list"
        params = {}
        for (k, a) in [
            ("user", user),
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
        if cluster_name is not None:
            params["cluster_name"] = cluster_name
        if job_id is not None:
            params["job_id"] = job_id
        return self._request(endpoint, params)

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
        if cluster_name is not None:
            params["cluster_name"] = cluster_name
        if job_id is not None:
            params["job_id"] = job_id
        # Due to current constraints, we have to pass "update_pairs"
        # as a string representing a structure in json.
        params["update_pairs"] = json.dumps(update_pairs)
        return self._request(endpoint, params, method="PUT")

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
        if cluster_name is not None:
            params["cluster_name"] = cluster_name
        return self._request(endpoint, params)

    def nodes_one(self, name: str = None, cluster_name: str = None) -> dict[str, any]:
        """REST call to api/v1/clusters/nodes/one.

        Gets the detailed description of a single node
        on the cluster specified. If there is no ambiguity
        with the name of the node, the cluster_name argument
        is not required.

        Args:
            name (str): Name of node to be described.
            cluster_name (str): Name of cluster where that node lives.

        Returns:
            dict[str,any]: Properties of the node, when valid.
            Otherwise returns an empty dict.
        """
        endpoint = "api/v1/clusters/nodes/one"
        params = {}
        if name is not None:
            params["name"] = name
        if cluster_name is not None:
            params["cluster_name"] = cluster_name
        return self._request(endpoint, params)
