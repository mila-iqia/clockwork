"""
This file contains a lot of arbitrary decisions that could change in the future.
"""

from collections import defaultdict
import re
import time

from flask.globals import current_app
from flask_login import current_user
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


def get_str_job_state(job_state):
    """
    Handle the different job state formats we retrieve accross the different Slurm versions
    """
    if isinstance(job_state, list) and len(job_state) > 0:
        return job_state[0]

    return job_state


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
    sort_asc=-1,
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

    # Get job user props
    if LD_jobs and current_user:
        user_props_map = {}
        # Collect all job user props related to found jobs,
        # and store them in a dict with keys (mila email username, job ID, cluster_name)
        for user_props in list(
            mc["job_user_props"].find(
                combine_all_mongodb_filters(
                    {
                        "job_id": {"$in": [job["slurm"]["job_id"] for job in LD_jobs]},
                        "mila_email_username": current_user.mila_email_username,
                    }
                )
            )
        ):
            key = (
                user_props["mila_email_username"],
                user_props["job_id"],
                user_props["cluster_name"],
            )
            assert key not in user_props_map
            user_props_map[key] = user_props["props"]

        if user_props_map:
            # Populate jobs with user props using
            # current user email, job ID and job cluster name
            # to find related user props in props map.
            for job in LD_jobs:
                key = (
                    current_user.mila_email_username,
                    job["slurm"]["job_id"],
                    job["slurm"]["cluster_name"],
                )
                if key in user_props_map:
                    job["job_user_props"] = user_props_map[key]

    # Set nbr_total_jobs
    if want_count:
        # Get the number of filtered jobs (not paginated)
        nbr_total_jobs = mc["jobs"].count_documents(mongodb_filter)
    else:
        # If want_count is False, nbr_total_jobs is None
        nbr_total_jobs = None

    # This handles the different format of jobs states we retrieve, through the different Slurm version
    for job in LD_jobs:
        if (
            isinstance(job["slurm"]["job_state"], list)
            and len(job["slurm"]["job_state"]) > 0
        ):
            job["slurm"]["job_state"] = job["slurm"]["job_state"][0]

    # Return the retrieved jobs and the number of unpagined jobs (if requested)
    return (LD_jobs, nbr_total_jobs)


def get_global_filter(
    username=None, job_ids=[], cluster_names=None, job_states=[], job_array=None
):
    """
    Set up a filter for MongoDB in order to filter username, clusters and job states,
    regarding what has been sent as parameter to the function.
    Important note: this function is just formatting the filter, it does not check
    whether or not the clusters, the job states and the username exist or are accessible.
    These checks must be done before.

    Parameters:
        username        ID of the user of whose jobs we want to retrieve
        job_ids         List of the IDs of the jobs we are looking for
        cluster_names   List of names of the clusters on which the expected jobs run/will run or have run
        job_states      List of names of job_states the expected jobs could have
        job_array       ID of job array in which we look for jobs

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
    if len(job_states) > 0:
        filters.append({"slurm.job_state": {"$in": job_states}})

    # Define the filter related to job array
    if job_array is not None:
        if job_array == 0:
            # Zero is default value for jobs without job arrays.
            # So, let's try to retrieve also jobs with job array not set (None value?)
            filters.append({"slurm.array_job_id": {"$in": [None, "0"]}})
        else:
            filters.append({"slurm.array_job_id": str(job_array)})

    # Combine the filters
    filter = combine_all_mongodb_filters(*filters)

    return filter


def get_jobs(
    username=None,
    job_ids=[],
    cluster_names=None,
    job_states=[],
    nbr_skipped_items=None,
    nbr_items_to_display=None,
    want_count=False,
    sort_by="submit_time",
    sort_asc=-1,
    job_array=None,
    user_prop_name=None,
    user_prop_content=None,
):
    """
    Set up the filters according to the parameters and retrieve the requested jobs from the database.

    Parameters:
        username                ID of the user of whose jobs we want to retrieve
        job_ids                 List of IDs of the jobs we are looking for
        cluster_names           List of names of the clusters on which the expected jobs run/will run or have run
        job_states              List of names of job states the expected jobs could have
        nbr_skipped_items       Number of jobs we want to skip in the result
        nbr_items_to_display    Number of requested jobs
        want_count              Whether or not the total jobs count is expected.
        sort_by                 Field to sort jobs. Sorted only if pagination is
                                defined.
        sort_asc                Whether or not to sort in ascending order (1)
                                or descending order (-1).
        job_array               ID of job array in which we look for jobs.
        user_prop_name          name of user prop (string) we must find in jobs to look for.
        user_prop_content       content of user prop (string) we must find in jobs to look for.

    Returns:
        A tuple containing:
            - the list of jobs as first entity
            - the total number of jobs corresponding of the filters in the databse, if want_count has been set to
            True, None otherwise, as second element
    """
    # If job user prop is specified,
    # get job indices from jobs associated to this prop.
    if user_prop_name is not None and user_prop_content is not None:
        mc = get_db()
        props_job_ids = [
            str(user_props["job_id"])
            for user_props in mc["job_user_props"].find(
                combine_all_mongodb_filters(
                    {f"props.{user_prop_name}": user_prop_content}
                )
            )
        ]
        if job_ids:
            # If job ids where provided, make intersection between given job ids and props job ids.
            job_ids = list(set(props_job_ids) & set(job_ids))
        else:
            # Otherwise, just use props job ids.
            job_ids = props_job_ids

    # Set up and combine filters
    filter = get_global_filter(
        username=username,
        job_ids=job_ids,
        cluster_names=cluster_names,
        job_states=job_states,
        job_array=job_array,
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


def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id"]
    return dict((k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


job_state_to_aggregated = {
    "BOOT_FAIL": "FAILED",
    "CANCELLED": "FAILED",
    "COMPLETED": "COMPLETED",
    "CONFIGURING": "PENDING",
    "COMPLETING": "RUNNING",
    "DEADLINE": "FAILED",
    "FAILED": "FAILED",
    "NODE_FAIL": "FAILED",
    "OUT_OF_MEMORY": "FAILED",
    "PENDING": "PENDING",
    "PREEMPTED": "FAILED",
    "RUNNING": "RUNNING",
    # Unsure what "RESV_DEL_HOLD: Job is being held after requested reservation
    # was deleted." means
    "RESV_DEL_HOLD": "PENDING",
    "REQUEUE_FED": "PENDING",
    "REQUEUE_HOLD": "PENDING",
    "REQUEUED": "PENDING",
    "RESIZING": "PENDING",
    "REVOKED": "FAILED",
    "SIGNALING": "RUNNING",
    "SPECIAL_EXIT": "FAILED",
    "STAGE_OUT": "RUNNING",
    "STOPPED": "FAILED",
    "SUSPENDED": "FAILED",
    "TIMEOUT": "FAILED",
}


def _make_job_states_mapping():
    results = defaultdict(set)
    for job_state, aggregated_job_state in job_state_to_aggregated.items():
        if aggregated_job_state is not None:
            results[aggregated_job_state].add(job_state)
    return results


aggregated_job_states_mapping = _make_job_states_mapping()


def get_inferred_job_states(global_job_states):
    """
    Get all the job states infered by the "global job states" provided as input.

    Parameter:
    - global_job_state  A list of strings referring to the "global state(s)" a job
                        could have, which are "RUNNING", "PENDING", "COMPLETED" and
                        "ERROR", which gather multiple job states according to the
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

    # For each requested "global job state", provide the associated "Slurm job states"
    for global_job_state in global_job_states:
        requested_slurm_job_states.extend(
            aggregated_job_states_mapping[global_job_state]
        )

    # Return the requested Slurm job states
    return requested_slurm_job_states


def get_inferred_job_state(job_state):
    """
    Return the Clockwork job state corresponding to a
    Slurm job state

    Parameter:
        job_state   The Slurm job state to convert

    Returns the associated Clockwork job state
    """
    return job_state_to_aggregated[get_str_job_state(job_state).upper()]


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
            "job_array",
            "job_user_props",
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
