import requests
import base64

class MilaTools:

    def __init__(self, config):
        self.config = config

        # TODO : When deployed for real, we might want to be a little more careful
        #        to protect people against sending http by accident to remote hosts.
        #        Not sure what the correct thing to do would be.
        if self.config['port'] == 443:
            http_or_https = "https"
        else:
            http_or_https = "http"

        self.complete_base_address = f"{http_or_https}://{self.config['host']}:{self.config['port']}"

    def _get_headers(self):

        # This is a common way to identify http requests.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization
        #
        # Note that the headers are hidden by TLS when using HTTPS
        # so they are not visible in transit.
        s = f"{self.config['email']}:{self.config['clockwork_api_key']}"
        encoded_bytes = base64.b64encode(s.encode("utf-8"))
        encoded_s = str(encoded_bytes, "utf-8")
        return {"Authorization": f"Basic {encoded_s}"}

    def _request(self, endpoint, params):

        if endpoint.startswith("/") or self.complete_base_address.endswith("/"):
            middle_slash = "" 
        else:
            middle_slash = "/"

        complete_address = f"{self.complete_base_address}{middle_slash}{endpoint}"
        response = requests.get(complete_address, params=params, headers=self._get_headers())
        print(response)
        # TODO : Check code instead and raise exception if it's the wrong one.
        if response.status_code == 200:
            return response.json()
        else:
            return None

    # For endpoints requiring `params` you'll pass the correct ones by specific arguments
    # to this function. This should help documenting expectations.
    def jobs_list(self):
        endpoint = "api/v1/clusters/jobs/list"
        params = {}
        return self._request(endpoint, params)

    def jobs_single_job(self, cluster_name, job_id):
        # TODO : I don't think that's implemented on the Flask server at the moment.
        endpoint = "api/v1/clusters/jobs/list"
        params = {"cluster_name": cluster_name, "job_id": job_id}
        return self._request(endpoint, params)
