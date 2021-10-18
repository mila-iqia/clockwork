"""
This file contains a lot of arbitrary decisions that could change in the future.

"""

import re
import time

from flask.globals import current_app
from ..db import get_db


def get_filter_cluster_name(cluster_name):
    if cluster_name is None:
        return {}
    else:
        return {"cluster_name": cluster_name}


def get_filter_job_id(job_id):
    """
    Add a check whether it's an integer or a string.
    """
    if job_id is None:
        return {}
    else:
        if re.match(r"^(\d*)$", job_id):
            return {"$or": [{"job_id": job_id}, {"job_id": int(job_id)}]}
        else:
            return {"job_id": job_id}


def get_filter_user(user):
    if user is None:
        return {}
    else:
        if user not in ["all", "*", ""]:
            return {
                "$or": [
                    {"mila_cluster_username": user},
                    {"cc_account_username": user},
                    {"mila_email_username": user},
                    {"mila_user_account": user},
                ]
            }
        else:
            return {}


def get_filter_time(time0):
    """
    We're calling the argument "time0" because "time" is already
    a python module, and we're using it in this very function.
    """
    if time0 is None:
        return {}
    else:
        # This can throw exceptions when "time0" is invalid.
        return {
            "$or": [
                {"end_time": {"$gt": int(time.time() - int(time0))}},
                {"end_time": 0},
            ]
        }


def combine_all_mongodb_filters(*mongodb_filters):
    """
    Creates a big AND clause if more than one argument is given.
    Drops out all the filters that are empty dict.
    """
    non_empty_mongodb_filters = [mf for mf in mongodb_filters if mf]
    if len(non_empty_mongodb_filters) == 0:
        return {}
    elif len(non_empty_mongodb_filters) == 1:
        return non_empty_mongodb_filters[0]
    else:
        return {"$and": list(non_empty_mongodb_filters)}


def get_mongodb_filter_from_query_filter(query_filter):
    """
    This is the logic that goes from the minimalistic description
    of what we want, coming from the web front, to produce
    the specific dict that we send to mongodb in order to retrieve
    exactly what we want.

    `query_filter` looks like
        {'time': 3600, 'user': 'all'}

    Please refer to the document "about_queries.md" to read more about
    the reasoning behing this function. It requires a document just by itself.
    """

    mongodb_filter_for_user = get_filter_user(query_filter.get("user", None))
    mongodb_filter_for_time = get_filter_time(query_filter.get("time", None))

    return combine_all_mongodb_filters(mongodb_filter_for_user, mongodb_filter_for_time)


def get_jobs(mongodb_filter: dict = {}):
    mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    return list(mc["jobs"].find(mongodb_filter))


def infer_best_guess_for_username(D_job):
    # TODO : We should perform some kind of mapping to Mila accounts or something.
    #        At the current time we're missing certain things to allow this to be done properly.
    # let's condense the three possible accounts into just one value
    for k in ["cc_account_username", "mila_cluster_username", "mila_email_username"]:
        if k in D_job and D_job[k] != "unknown":
            D_job["best_guess_for_username"] = D_job[k]
            return D_job
    # failed to find something better than that
    D_job["best_guess_for_username"] = "unknown"
    return D_job


def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id", "grafana_helpers"]
    return dict((k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


def get_job_state_totals(
    L_entries,
    mapping={
        "PENDING": "PENDING",
        "RUNNING": "RUNNING",
        "COMPLETING": "RUNNING",
        "COMPLETED": "COMPLETED",
        "OUT_OF_MEMORY": "ERROR",
        "TIMEOUT": "ERROR",
        "FAILED": "ERROR",
        "CANCELLED": "ERROR",
    },
):
    """
    This function doesn't make much sense if you don't filter anything ahead of time.
    Otherwise you'll get values for jobs that have been over for very long.
    """

    # create a table with one entry for each entry
    mila_user_accounts = set(e["mila_user_account"] for e in L_entries)
    DD_counts = dict(
        (mila_user_account, {"PENDING": 0, "RUNNING": 0, "COMPLETED": 0, "ERROR": 0})
        for mila_user_account in mila_user_accounts
    )
    for e in L_entries:
        DD_counts[e["mila_user_account"]][mapping[e["job_state"]]] += 1

    return DD_counts
