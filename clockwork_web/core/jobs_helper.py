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
        return {"slurm.cluster_name": cluster_name}


def get_filter_job_id(job_id):
    """
    Add a check whether it's an integer or a string.
    """
    if job_id is None:
        return {}
    else:
        return {"slurm.job_id": job_id}


def get_filter_after_end_time(end_time):
    """
    Returns all the matches that either don't have
    an entry for "end_time" (i.e. they're waiting to be
    scheduled or they're running now), or the ones
    that have an "end_time" that's more recent than the
    `end_time` argument.

    The `end_time` argument is usually something like
    `int(time.time() - 3600)` in order to get all the
    entries dating from an hour ago or more recent than that.
    """
    if end_time is None:
        return {}
    else:
        # This can throw exceptions when "end_time" is invalid.
        return {
            "$or": [
                {"slurm.end_time": {"$gt": end_time}},
                {"slurm.end_time": None},
            ]
        }


def combine_all_mongodb_filters(*mongodb_filters):
    """
    Creates a big AND clause if more than one argument is given.
    Drops out all the filters that are empty dict.

    Parameters:
        mongodb_filters     One or more filter(s) we want to combine

    Return:
        A concatenation of the filters given as input
    """
    non_empty_mongodb_filters = [mf for mf in mongodb_filters if mf]
    if len(non_empty_mongodb_filters) == 0:
        return {}
    elif len(non_empty_mongodb_filters) == 1:
        return non_empty_mongodb_filters[0]
    else:
        return {"$and": non_empty_mongodb_filters}


def get_jobs(
    mongodb_filter: dict = {},
    nbr_skipped_items=None,
    nbr_items_to_display=None,
    count=False,
):
    """
    Talk to the database and get the information.

    Parameters:
        mongodb_filter          A concatenation of the filters to apply in order
                                to select the jobs we want to retrieve from the
                                MongoDB database
        nbr_skipped_items       Number of elements to skip while listing the jobs
        nbr_items_to_display    Number of jobs to display
        count                   Whether or not we are interested by the number of
                                unpagined jobs. If it is True, the result is a tuple
                                (jobs_list, count). Otherwise, only the jobs list
                                is returned

    Returns:
        Returns a list of dict with the properties of jobs.
    """
    # Assert that the two pagination elements (nbr_skipped_items and
    # nbr_items_to_display) are respectively positive and strictly positive
    # integers
    if not (type(nbr_skipped_items) == int and nbr_skipped_items >= 0):
        nbr_skipped_items = None

    if not (type(nbr_items_to_display) == int and nbr_items_to_display > 0):
        nbr_items_to_display = None

    # Retrieve the database
    mc = get_db()
    # Get the jobs from it
    if nbr_skipped_items != None and nbr_items_to_display:
        LD_jobs = list(
            mc["jobs"]
            .find(mongodb_filter)
            .skip(nbr_skipped_items)
            .limit(nbr_items_to_display)
        )

    else:
        LD_jobs = list(mc["jobs"].find(mongodb_filter))

    if count:
        # Get the number of filtered jobs (not paginated)
        nbr_total_jobs = mc["jobs"].count_documents(mongodb_filter)

        # Return the retrieved jobs and the number of unpagined jobs
        return (LD_jobs, nbr_total_jobs)

    # Return the retrieved jobs
    return LD_jobs


def update_job_user_dict(mongodb_filter: dict, new_user_dict: dict):
    """
    This is a step that happens after every checks have been made.
    It's the "now we actually do it" part of the sequence of operations.

    `mongodb_filter` is to identify a job uniquely
    `new_user_dict` is the value to replace the "user" field with
    """
    mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    return mc["jobs"].update_one(
        mongodb_filter, {"$set": {"user": new_user_dict}}, upsert=False
    )


def infer_best_guess_for_username(D_job):
    """
    Mutates the argument by adding the "best_guess_for_username" field.
    """

    # TODO : Rethink this "feature" that's mostly
    # tied to the web interface to display something
    # useful to the users. CW-81
    for k in ["cc_account_username", "mila_cluster_username", "mila_email_username"]:
        if k in D_job["cw"] and D_job["cw"][k] not in [None, "unknown"]:
            D_job["cw"]["best_guess_for_username"] = D_job["cw"][k]
            return D_job
    # failed to find something better than that
    D_job["cw"]["best_guess_for_username"] = "unknown"
    return D_job


def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id"]
    return dict((k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


# def get_job_state_totals(
#     L_entries,
#     mapping={
#         "PENDING": "PENDING",
#         "RUNNING": "RUNNING",
#         "COMPLETING": "RUNNING",
#         "COMPLETED": "COMPLETED",
#         "OUT_OF_MEMORY": "ERROR",
#         "TIMEOUT": "ERROR",
#         "FAILED": "ERROR",
#         "CANCELLED": "ERROR",
#     },
# ):
# ):
#     """
#     This function doesn't make much sense if you don't filter anything ahead of time.
#     Otherwise you'll get values for jobs that have been over for very long.
#
#     2021-12-01 : Note that this function is currently not being used anywhere.
#     """
#
#     # create a table with one entry for each entry
#     mila_cluster_usernames = set(e["cw"]["mila_cluster_username"] for e in L_entries)
#     DD_counts = dict(
#         (mila_cluster_username, {"PENDING": 0, "RUNNING": 0, "COMPLETED": 0, "ERROR": 0})
#         for mila_cluster_username in mila_cluster_usernames
#     )
#     for e in L_entries:
#         DD_counts[e["mila_cluster_username"]][mapping[e["job_state"]]] += 1
#
#     return DD_counts
