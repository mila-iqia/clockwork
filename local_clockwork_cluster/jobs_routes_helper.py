"""
This file contains a lot of arbitrary decisions that could change in the future.

"""

from mongo_client import get_mongo_client


def get_jobs(find_filter:dict={}):
    mc = get_mongo_client()
    mc_db = mc['slurm']
    return list(mc_db["jobs"].find(find_filter))


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

