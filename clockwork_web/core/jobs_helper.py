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


def get_filtered_and_paginated_jobs(
    mongodb_filter: dict = {},
    nbr_skipped_items=None,
    nbr_items_to_display=None,
    want_count=False,
    sort_by="submit_time",
    sort_asc=1,
):
    """
    Talk to the database and get the information.

    Parameters:
        mongodb_filter          A concatenation of the filters to apply in order
                                to select the jobs we want to retrieve from the
                                MongoDB database
        nbr_skipped_items       Number of elements to skip while listing the jobs
        nbr_items_to_display    Number of jobs to display
        want_count              Whether or not we are interested by the number of
                                unpaginated jobs.
        sort_by                 Field to sort jobs. Sorted only if pagination is
                                defined.
        sort_asc                Whether or not to sort in ascending order (1)
                                or descending order (-1).

    Returns:
        Returns a tuple (jobs_list, jobs_count or None).
        The first element is a list of dictionaries with the properties of jobs.
        In general we expect len(jobs_list) to be nbr_items_to_display if
        we found sufficiently many matches.

        The second element contains the total number of jobs found with the mongodb_filter,
        counting the whole database and not just one page. It is None if want_count is False.

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
        # Check sorting parameters
        assert sort_by in {
            "cluster_name",
            "user",
            "job_id",
            "name",  # job name
            "job_state",
            "submit_time",
            "start_time",
            "end_time",
        }
        assert sort_asc in (-1, 1)
        # Set sorting
        if sort_by == "user":
            sorting = [["cw.mila_email_username", sort_asc]]
        else:
            sorting = [[f"slurm.{sort_by}", sort_asc]]
        # Is sorting is not by job_id, add supplementary sorting
        if sort_by != "job_id":
            sorting.append(["slurm.job_id", 1])
        LD_jobs = list(
            mc["jobs"]
            .find(mongodb_filter)
            .sort(sorting)
            .skip(nbr_skipped_items)
            .limit(nbr_items_to_display)
        )

    else:
        # Here we don't want to sort the results because we are returning
        # all of them to the user. Sorting would impose a cost to the MongoDB server
        # and since we are returning all the matches, the client can sort
        # the results locally if they wish.
        # Moreover, in situations where a lot of data was present,
        # e.g. 1-2 months of historical data, this has caused errors
        # on the server because not enough memory was allocated to perform the sorting.
        LD_jobs = list(mc["jobs"].find(mongodb_filter))

    # Set nbr_total_jobs
    if want_count:
        # Get the number of filtered jobs (not paginated)
        nbr_total_jobs = mc["jobs"].count_documents(mongodb_filter)
    else:
        # If want_count is False, nbr_total_jobs is None
        nbr_total_jobs = None

    # Return the retrieved jobs and the number of unpagined jobs (if requested)
    return (LD_jobs, nbr_total_jobs)


def get_global_filter(username=None, job_ids=[], cluster_names=None, states=[]):
    """
    Set up a filter for MongoDB in order to filter username, clusters and job states,
    regarding what has been sent as parameter to the function.
    Important note: this function is just formatting the filter, it does not check
    whether or not the clusters, the states and the username exist or are accessible. These
    checks must be done before.

    Parameters:
        username        ID of the user of whose jobs we want to retrieve
        job_ids         List of the IDs of the jobs we are looking for
        cluster_names   List of names of the clusters on which the expected jobs run/will run or have run
        states          List of names of states the expected jobs could have

    Returns:
        A dictionary containing the conditions to be applied on the search.
        (See MongoDB Query documents: https://www.mongodb.com/docs/manual/tutorial/query-documents/)
    """
    # Initialize the filters list
    filters = []

    # Define the user filter
    if username is not None:
        filters.append({"cw.mila_email_username": username})

    # Define the filter related to the IDs of the jobs we are looking for
    if len(job_ids) > 0:
        filters.append({"slurm.job_id": {"$in": job_ids}})

    # Define the filter related to the cluster on which the jobs run
    if cluster_names is not None:
        filters.append({"slurm.cluster_name": {"$in": cluster_names}})

    # Define the filter related to the jobs' states
    if len(states) > 0:
        all_inferred_states = get_inferred_job_states(states)
        filters.append({"slurm.job_state": {"$in": all_inferred_states}})

    # Combine the filters
    filter = combine_all_mongodb_filters(*filters)

    return filter


def get_jobs(
    username=None,
    job_ids=[],
    cluster_names=None,
    states=[],
    nbr_skipped_items=None,
    nbr_items_to_display=None,
    want_count=False,
    sort_by="submit_time",
    sort_asc=1,
):
    """
    Set up the filters according to the parameters and retrieve the requested jobs from the database.

    Parameters:
        username                ID of the user of whose jobs we want to retrieve
        job_ids                 List of IDs of the jobs we are looking for
        cluster_names           List of names of the clusters on which the expected jobs run/will run or have run
        states                  List of names of states the expected jobs could have
        nbr_skipped_items       Number of jobs we want to skip in the result
        nbr_items_to_display    Number of requested jobs
        want_count              Whether or not the total jobs count is expected.
        sort_by                 Field to sort jobs. Sorted only if pagination is
                                defined.
        sort_asc                Whether or not to sort in ascending order (1)
                                or descending order (-1).

    Returns:
        A tuple containing:
            - the list of jobs as first entity
            - the total number of jobs corresponding of the filters in the databse, if want_count has been set to
            True, None otherwise, as second element
    """
    # Set up and combine filters
    filter = get_global_filter(
        username=username, job_ids=job_ids, cluster_names=cluster_names, states=states
    )
    # Retrieve the jobs from the filters and return them
    # (The return value is a tuple (LD_jobs, nbr_total_jobs))
    return get_filtered_and_paginated_jobs(
        mongodb_filter=filter,
        nbr_skipped_items=nbr_skipped_items,
        nbr_items_to_display=nbr_items_to_display,
        want_count=want_count,
        sort_by=sort_by,
        sort_asc=sort_asc,
    )


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


def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id"]
    return dict((k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


def get_inferred_job_states(global_job_states):
    """
    Get all the job states infered by the "global job states" provided as input.

    Parameter:
    - global_job_state  A list of strings referring to the "global state(s)" a job
                        could have, which are "RUNNING", "PENDING", "COMPLETED" and
                        "ERROR", which gather multiple states according to the
                        following mapping:
                        {
                            "PENDING": "PENDING",
                            "PREEMPTED": "FAILED",
                            "RUNNING": "RUNNING",
                            "COMPLETING": "RUNNING",
                            "COMPLETED": "COMPLETED",
                            "OUT_OF_MEMORY": "FAILED",
                            "TIMEOUT": "FAILED",
                            "FAILED": "FAILED",
                            "CANCELLED": "FAILED"
                        }

    Return
        The list of Slurm job states associated to the global job states provided as
        input
    """
    # Initialize the "Slurm job states" associated to the "global job states" provided as input
    requested_slurm_job_states = []

    # Define the mapping between the job states and the gathered job states
    states_mapping = {
        "PENDING": ["PENDING"],
        "RUNNING": ["RUNNING", "COMPLETING"],
        "COMPLETED": ["COMPLETED"],
        "FAILED": ["CANCELLED", "FAILED", "OUT_OF_MEMORY", "TIMEOUT", "PREEMPTED"],
    }

    # For each requested "global job state", provide the associated "Slurm job states"
    for global_job_state in global_job_states:
        requested_slurm_job_states.extend(states_mapping[global_job_state])

    # Return the requested Slurm states
    return requested_slurm_job_states


def get_jobs_properties_list_per_page():
    """
    Get the list of the displayable jobs properties for the dashboard
    and the jobs list page.

    Returns
        A dictionary associating a list of jobs properties names
        to a page name (here "dashboard" or "jobs_list")
    """
    return {
        "dashboard": [
            "clusters",
            "job_id",
            "job_name",
            "job_state",
            "start_time",
            "submit_time",
            "end_time",
            "links",
            "actions",
        ],
        "jobs_list": [
            "clusters",
            "user",
            "job_id",
            "job_name",
            "job_state",
            "start_time",
            "submit_time",
            "end_time",
            "links",
            "actions",
        ],
    }


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
