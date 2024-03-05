from pprint import pprint
import re
import os
import json
import requests
import time
import logging
from collections import defaultdict

# Use of "Markup" described there to avoid Flask escaping it when passing to a template.
# https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2
from markupsafe import Markup
from flask import Flask, Response, url_for, request, redirect, make_response
from flask import request, send_file
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper

# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g

from flask_login import (
    current_user,
    login_required,
)
from clockwork_web.core.search_helper import search_request
from flask_babel import gettext

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.utils import to_boolean, get_custom_array_from_request_args
from clockwork_web.core.users_helper import render_template_with_user_settings

flask_api = Blueprint("jobs", __name__)

from clockwork_web.core.jobs_helper import (
    get_filter_after_end_time,
    get_filter_cluster_name,
    get_filter_job_id,
    combine_all_mongodb_filters,
    strip_artificial_fields_from_job,
    get_jobs,
    get_inferred_job_states,
)
from clockwork_web.core.pagination_helper import get_pagination_values


@flask_api.route("/")
@login_required
def route_index():
    """
    Not implemented, but this will be the new name for the jobs.html with interactions.
    """
    logging.info(
        f"clockwork browser route: /jobs/ - current_user={current_user.mila_email_username}"
    )
    return redirect("dashboard")


@flask_api.route("/search")
@login_required
def route_search():
    """
    Display a list of jobs, which can be filtered by user, cluster and job state.

    Can take optional arguments:
    - "username" refers to the Mila username, identifying the user
    - "cluster_name" refers to the cluster(s) on which we are looking for the jobs
    - "aggregated_job_state" refers to the state(s) of the jobs we are looking for. Here are concerned
      the "global job states", which are "RUNNING", "PENDING", "COMPLETED" and "FAILED", which
      gather multiple job states according to the following mapping:
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
    - "page_num" is optional and used for the pagination: it is a positive integer
      presenting the number of the current page
    - "nbr_items_per_page" is optional and used for the pagination: it is a
      positive integer presenting the number of items to display per page
    - "want_json" is set to True if the expected returned entity is a JSON list of the jobs
    - "want_count" is useful when want_json is True. If want_count is True, the returned JSON
      has the following format:
        {
            "jobs": [{<job_1>}, ..., {<job_n>}],
            "nbr_total_jobs": n
        }
    - "sort_by" is optional and used to specify sorting field (default "submit_time").
      Allowed values: "cluster_name", "user", "job_id", "name" (for job name), "job_state",
      "submit_time", "start_time", "end_time"
    - "sort_asc" is an optional integer and used to specify if sorting is
      ascending (1) or descending (-1). Default is 1.
    - "job_array" is optional and used to specify the job array in which we are looking for jobs
    - "job_label" is optional and used to specify the label associated to jobs we are looking for

    .. :quickref: list all Slurm job as formatted html
    """
    logging.info(
        f"clockwork browser route: /jobs/search - current_user={current_user.mila_email_username}"
    )

    ###########################
    # Retrieve the parameters #
    ###########################

    # Retrieve the format requested to return the information
    want_json = request.args.get(
        "want_json", type=str, default="False"
    )  # If True, the user wants a JSON output
    want_json = to_boolean(want_json)

    ################################################
    # Retrieve the jobs and display or return them #
    ################################################

    (query, LD_jobs, nbr_total_jobs) = search_request(
        current_user,
        request.args,
        # The default pagination parameters are different whether or not a JSON response is requested.
        # This is because we are using `want_json=True` along with no pagination arguments for a special
        # case when we want to retrieve all the jobs in the dashboard for a given user.
        # There is a certain notion with `want_json` that we are retrieving the data for the purposes
        # of listing them exhaustively, and not just for displaying them with scroll bars in some HTML page.
        force_pagination=not want_json,
    )

    LD_jobs = [strip_artificial_fields_from_job(D_job) for D_job in LD_jobs]

    if want_json:
        # If requested, return the list as JSON
        if query.want_count:
            # If the number of all the jobs is requested, return the jobs list
            # and the number of jobs
            return {"jobs": LD_jobs, "nbr_total_jobs": nbr_total_jobs}

        else:
            # Otherwise, only the jobs list is returned
            return jsonify(LD_jobs)
    else:
        # Display the HTML page
        return render_template_with_user_settings(
            "jobs_search.html",
            LD_jobs=LD_jobs,
            mila_email_username=current_user.mila_email_username,
            page_num=query.pagination_page_num,
            nbr_total_jobs=nbr_total_jobs,
            previous_request_args={
                "username": query.username,
                "cluster_name": query.cluster_name,
                "aggregated_job_state": query.aggregated_job_state,
                "page_num": query.pagination_page_num,
                "nbr_items_per_page": query.pagination_nbr_items_per_page,
                "want_json": want_json,
                "want_count": query.want_count,
                "sort_by": query.sort_by,
                "sort_asc": query.sort_asc,
                "job_array": query.job_array,
                "job_label": query.job_label,
            },
        )


@flask_api.route("/one")
@login_required
def route_one():
    """
    Takes args "cluster_name", "job_id".
    This can work with only "job_id" if it's unique,
    but otherwise it might require specifying the cluster name.
    Note that this returns a page with only the "slurm" component
    because we had troubles using the templates correctly with dicts.

    Besides, it's unclear what we're supposed to do with the extra
    "cw" and "user" fields when it comes to displaying them as html.
    See CW-82.

    .. :quickref: list one Slurm job as formatted html
    """
    logging.info(
        f"clockwork browser route: /jobs/one - current_user={current_user.mila_email_username}"
    )

    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Retrieve the given job ID
    job_ids = get_custom_array_from_request_args(request.args.get("job_id"))
    previous_request_args["job_id"] = job_ids

    # Retrieve the given cluster names
    requested_cluster_names = get_custom_array_from_request_args(
        request.args.get("cluster_name")
    )
    if len(requested_cluster_names) < 1:
        # If no cluster has been requested, then all clusters have been requested
        # (a filter related to which clusters are available to the current user
        #  is then applied)
        requested_cluster_names = get_all_clusters()

    # Limit the cluster options to the clusters the user can access
    user_clusters = (
        current_user.get_available_clusters()
    )  # Retrieve the clusters the user can access
    cluster_names = [
        cluster for cluster in requested_cluster_names if cluster in user_clusters
    ]
    previous_request_args["cluster_name"] = cluster_names

    # Check the job_id input
    if len(job_ids) < 1:
        # Return an error if no job ID has been given
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("Missing argument job_id."),
                previous_request_args=previous_request_args,
                error_code=400,
            ),
            400,
        )  # bad request
    elif len(job_ids) > 1:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("Too many job_ids have been requested."),
                previous_request_args=previous_request_args,
            ),
            400,
        )  # bad request

    # Set up the filters and retrieve the expected job
    (LD_jobs, _) = get_jobs(job_ids=job_ids, cluster_names=cluster_names)

    # Return error messages if the number of retrieved jobs is 0 or more than 1
    if len(LD_jobs) == 0:
        return render_template_with_user_settings(
            "error.html",
            error_msg=gettext("Found no job with job_id %(expected_job_id)s.")
            % {"expected_job_id": job_ids[0]},
            previous_request_args=previous_request_args,
        )

    if len(LD_jobs) > 1:
        return render_template_with_user_settings(
            "error.html",
            error_msg=gettext(
                "Found %(len_LD_jobs) jobs with job_id %(job_id)."
            ).format(len_LD_jobs=len(LD_jobs), job_id=job_ids[0]),
            previous_request_args=previous_request_args,
        )  # Not sure what to do about these cases.

    D_job = strip_artificial_fields_from_job(LD_jobs[0])

    # let's sort alphabetically by keys
    LP_single_job_slurm = list(sorted(D_job["slurm"].items(), key=lambda e: e[0]))
    D_single_job_cw = D_job["cw"]
    # Add an element "cw_username" to D_job["cw"] in order to avoid additional
    # operations in the template
    if (
        "mila_email_username" in D_single_job_cw
        and D_single_job_cw["mila_email_username"]
    ):
        D_single_job_cw["mila_username"] = D_single_job_cw["mila_email_username"].split(
            "@"
        )[0]

    return render_template_with_user_settings(
        "single_job.html",
        LP_single_job_slurm=LP_single_job_slurm,
        D_single_job_cw=D_single_job_cw,
        job_id=job_ids[0],
        mila_email_username=current_user.mila_email_username,
        previous_request_args=previous_request_args,
    )


@flask_api.route("/dashboard")
@login_required
def route_dashboard():
    """
    Displays the list of the current user's jobs.
    """
    logging.info(
        f"clockwork browser route: /jobs/dashboard - current_user={current_user.mila_email_username}"
    )

    return render_template_with_user_settings(
        "dashboard.html",
        mila_email_username=current_user.mila_email_username,
    )
