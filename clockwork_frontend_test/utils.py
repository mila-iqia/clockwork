import json, os
from datetime import datetime

# Generate base url depending on whether we are inside docker container or not.
IN_DOCKER = os.environ.get("WE_ARE_IN_DOCKER", False)
BASE_URL = f"http://127.0.0.1:{5000 if IN_DOCKER else 15000}"


def get_fake_data():
    # Retrieve the fake data content
    with open("test_common/fake_data.json", "r") as infile:
        return json.load(infile)


def get_default_display_date(input_date):
    if input_date == None:
        return ""
    elif input_date == 0:
        # If the timestamp is 0, does not display a time
        return ""
    else:
        return datetime.fromtimestamp(input_date).strftime(
            "%Y/%m/%d %H:%M"
        )  # The format is YYYY/MM/DD hh:mm


def get_user_jobs_search_default_table(username):
    """
    Retrieve the 40 last submitted jobs of a specific user.

    Parameters:
        username:   The mail of the user, used as an ID

    Return:
        A list containing the 40 last submitted jobs of a specific user
    """
    # Sorts the jobs by submit time
    sorted_jobs = sorted(
        get_fake_data()["jobs"],
        key=lambda j: (-j["slurm"]["submit_time"], j["slurm"]["job_id"]),
    )

    return [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted_jobs
        if job["cw"]["mila_email_username"] == username
    ][:40]


def get_admin_username():
    # Retrieve an admin from the fake_data
    for user in get_fake_data()["users"]:
        if "admin_access" in user and user["admin_access"]:
            return user["mila_email_username"]


def is_admin(username):
    """
    Check in the fake data if a user is an admin
    """
    for user in get_fake_data()["users"]:
        if user["mila_email_username"] == username:
            return "admin_access" in user and user["admin_access"]
    return False


def get_language(username):
    """
    Retrieve the language of a user

    Parameter:
        username    The username of the user we want to retrieve the language of

    Returns the language ("en" or "fr") used by the user
    """
    for user in get_fake_data()["users"]:
        if user["mila_email_username"] == username:
            return user["web_settings"]["language"]
