"""
Script using locust framework to benchmark a clockwork server.

Usage:
```
CLOCKWORK_EMAIL='<your-email>' CLOCKWORK_API_KEY='<your-api-key>' locust -f scripts/server_benchmark_locust.py
```

Locust documentation: https://docs.locust.io/en/stable/index.html
"""
import json

import base64
import urllib.parse
import os

try:
    from locust import FastHttpUser, task, events
except Exception:
    print(
        "locust needed. You can install it with `pip install locust`."
        "More info: https://docs.locust.io/en/stable/index.html"
    )
    raise
try:
    from clockwork_tools.client import ClockworkToolsClient
except Exception:
    print(
        "Clockwork tools needed. You can install it with `cd clockwork_tools` then `pip install -e .`"
    )
    raise


# Path used to store a dictionary mapping a server URL to server config
# (server credentials and usernames).
LOCUST_CONFIG_FILE = os.path.abspath("tmp/locust.config.json")

USERNAMES = []
NEXT_USER_ID = 0
EMAIL = None
API_KEY = None


@events.test_start.add_listener
def _(environment, **kwargs):
    """Initialize locust.

    Get server config and save it in locust config file if necessary."""

    global USERNAMES
    global NEXT_USER_ID
    global EMAIL
    global API_KEY

    locust_config = {}
    host_config = {}
    if os.path.isfile(LOCUST_CONFIG_FILE):
        with open(LOCUST_CONFIG_FILE) as file:
            locust_config = json.load(file)
        if environment.host in locust_config:
            host_config = locust_config[environment.host]
            print(
                f"Loaded config for url {environment.host} from locust config file {LOCUST_CONFIG_FILE}"
            )

    if not host_config:
        print("Get available users")
        url_info = urllib.parse.urlsplit(environment.host)
        print(
            "Server:",
            environment.host,
            "url:",
            url_info.hostname,
            "port:",
            url_info.port,
        )
        client = ClockworkToolsClient(host=url_info.hostname, port=url_info.port or 80)
        jobs = client.jobs_list()
        print(f"Initial number of jobs: {len(jobs)}")
        # Get and sort users. Remove `None`, because a job may have no user.
        users = sorted({job["cw"]["mila_email_username"] for job in jobs} - {None})
        host_config = {
            "email": client.email,
            "api_key": client.clockwork_api_key,
            "usernames": users,
        }
        locust_config[environment.host] = host_config

        os.makedirs(os.path.dirname(LOCUST_CONFIG_FILE), exist_ok=True)
        with open(LOCUST_CONFIG_FILE, "w") as file:
            json.dump(locust_config, file)
        print(f"Saved locust config in {LOCUST_CONFIG_FILE}")

    EMAIL = host_config["email"]
    API_KEY = host_config["api_key"]
    USERNAMES = host_config["usernames"]
    NEXT_USER_ID = 0
    print(f"Available users: {len(USERNAMES)}")


class ClockworkUser(FastHttpUser):
    def __init__(self, *args, **kwargs):
        """Initialize user.

        Get username to use for this user
        """
        global NEXT_USER_ID
        super().__init__(*args, **kwargs)
        self.username = USERNAMES[NEXT_USER_ID % len(USERNAMES)]
        # self.username = EMAIL
        # Move to next username for next user
        NEXT_USER_ID += 1
        print("Username:", NEXT_USER_ID, self.username)

    @task
    def get_jobs(self):
        resp = self.client.get(
            "/api/v1/clusters/jobs/list",
            params={"username": self.username},
            headers=self._get_headers(),
        )
        jobs = resp.json()
        assert isinstance(jobs, list)
        assert jobs
        assert jobs[0]["cw"]["mila_email_username"] == self.username

    @staticmethod
    def _get_headers():
        """Get authentication headers.

        NB: A user authenticated using CLOCKWORK_EMAIL and CLOCKWORK_API_KEY can list jobs
        from other users. So, user associated to a ClockworkUser instance (defined in `self.username`)
        does not need to be the user who is currently authenticated.
        """
        encoded_bytes = base64.b64encode(f"{EMAIL}:{API_KEY}".encode("utf-8"))
        encoded_s = str(encoded_bytes, "utf-8")
        return {"Authorization": f"Basic {encoded_s}"}
