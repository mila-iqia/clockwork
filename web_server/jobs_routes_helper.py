"""
This file contains a lot of arbitrary decisions that could change in the future.

"""

import time

from flask.globals import current_app
from db import get_db


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

    if 'user' in query_filter and query_filter['user'] not in ["all", "*", ""]:
        user = query_filter['user']

        mongodb_filter_for_user = {
            '$or': [{'mila_cluster_username': user}, 
                    {'cc_account_username': user}, 
                    {'mila_email_username': user}, 
                    {'mila_user_account': user}]
            }
    else:
        mongodb_filter_for_user = {}

    
    if 'time' in query_filter:
        mongodb_filter_for_time = {
            '$or' : [   {'end_time': {'$gt': int(time.time() - query_filter['time'])}},
                        {'end_time': 0}]
            }
    else:
        mongodb_filter_for_time = {}


    # Let's add a AND clause only if needed.
    # If any of the two dict are empty, just
    # return the other one.
    # If neither are empty, then use that AND clause.
    if not mongodb_filter_for_user:
        return mongodb_filter_for_time
    elif not mongodb_filter_for_time:
        return mongodb_filter_for_user
    else:
        return {'$and': [mongodb_filter_for_user, mongodb_filter_for_time]}


def get_jobs(mongodb_filter:dict={}):
    mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    return list(mc["jobs"].find(mongodb_filter))


def infer_best_guess_for_username(D_job):
    # TODO : We should perform some kind of mapping to Mila accounts or something.
    #        At the current time we're missing certain things to allow this to be done properly.
    # let's condense the three possible accounts into just one value
    for k in ['cc_account_username', 'mila_cluster_username', 'mila_email_username']:
        if k in D_job and D_job[k] != 'unknown':
            D_job['best_guess_for_username'] = D_job[k]
            return D_job
    # failed to find something better than that
    D_job['best_guess_for_username'] = 'unknown'
    return D_job

def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id", "grafana_helpers"]
    return dict( (k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


def get_job_state_totals(L_entries,
    mapping={
        "PENDING": "PENDING",
        "RUNNING": "RUNNING",
        "COMPLETING": "RUNNING",
        "COMPLETED": "COMPLETED",
        "OUT_OF_MEMORY": "ERROR",
        "TIMEOUT": "ERROR",
        "FAILED": "ERROR",
        "CANCELLED": "ERROR"}
    ):
    """
    This function doesn't make much sense if you don't filter anything ahead of time.
    Otherwise you'll get values for jobs that have been over for very long.
    """

    # create a table with one entry for each entry    
    mila_user_accounts = set(e["mila_user_account"] for e in L_entries)
    DD_counts = dict((mila_user_account, {"PENDING":0, "RUNNING":0, "COMPLETED":0, "ERROR":0}) for mila_user_account in mila_user_accounts)
    for e in L_entries:
        DD_counts[e["mila_user_account"]][mapping[e["job_state"]]] += 1

    return DD_counts

