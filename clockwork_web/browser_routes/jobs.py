from pprint import pprint
import re
import os
import json
import requests
import time
from collections import defaultdict


# Use of "Markup" described there to avoid Flask escaping it when passing to a template.
# https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
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
from flask_babel import gettext

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

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
    infer_best_guess_for_username,
)
from clockwork_web.core.pagination_helper import get_pagination_values


@flask_api.route("/")
@login_required
def route_index():
    """
    Not implemented, but this will be the new name for the jobs.html with interactions.
    """
    return redirect("interactive")


@flask_api.route("/list")
@login_required
def route_list():
    """
    Can take optional args "cluster_name", "user", "relative_time".

    "user" refers to any of the three alternatives to identify a user,
    and it will match any of them.
    "relative_time" refers to how many seconds to go back in time to list jobs.
    "want_json" is set to True if the expected returned entity is a JSON list of the jobs.
    "page_num" is optional and used for the pagination: it is a positive integer
    presenting the number of the current page
    "nbr_items_per_page" is optional and used for the pagination: it is a
    positive integer presenting the number of items to display per page

    .. :quickref: list all Slurm job as formatted html
    """
    # Define the type of the return
    want_json = request.args.get("want_json", type=str, default="False")
    want_json = to_boolean(want_json)

    # Retrieve the pagination parameters
    pagination_page_num = request.args.get("page_num", type=int, default="1")
    pagination_nbr_items_per_page = request.args.get("nbr_items_per_page", type=int)
    # Use the pagination helper to define the number of element to skip, and the number of elements to display
    (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
        current_user.mila_email_username,
        pagination_page_num,
        pagination_nbr_items_per_page,
    )

    # Define the filter to select the jobs
    user_name = request.args.get("user", None)
    if user_name is not None:
        f0 = {"cw.mila_email_username": user_name}
    else:
        f0 = {}

    time1 = request.args.get("relative_time", None)
    if time1 is None:
        f1 = {}
    else:
        try:
            time1 = float(time1)
            f1 = get_filter_after_end_time(end_time=time.time() - time1)
        except Exception as inst:
            print(inst)
            return (
                render_template_with_user_settings(
                    "error.html",
                    error_msg=gettext(
                        "Field 'relative_time' cannot be cast as a valid integer: %(time1)."
                    ).format(time1=time1),
                ),
                400,
            )  # bad request

    # Combine the filters
    filter = combine_all_mongodb_filters(f0, f1)

    # Retrieve the jobs, by applying the filters and the pagination
    LD_jobs = get_jobs(
        filter,
        nbr_skipped_items=nbr_skipped_items,
        nbr_items_to_display=nbr_items_to_display,
    )

    # TODO : You might want to stop doing the `infer_best_guess_for_username`
    # at some point to design something better. See CW-81.
    LD_jobs = [
        infer_best_guess_for_username(strip_artificial_fields_from_job(D_job))
        for D_job in LD_jobs
    ]

    if want_json:
        # If requested, return the list as JSON
        return jsonify(LD_jobs)
    else:
        # Otherwise, display the HTML page
        return render_template_with_user_settings(
            "jobs.html",
            LD_jobs=LD_jobs,
            mila_email_username=current_user.mila_email_username,
            page_num=pagination_page_num,
        )


@flask_api.route("/search")
@login_required
def route_search():
    """
    Display a list of jobs, which can be filtered by user, cluster and state.

    Can take optional arguments:
    - "user_name"
    - "clusters_names"
    - "states"
    - "page_num"
    - "nbr_items_per_page".

    - "user_name" refers to any of the three alternatives to identify a user,
      and it will match any of them.
    - "clusters_names" refers to the cluster(s) on which we are looking for the jobs
    - "states" refers to the state(s) of the jobs we are looking for
    - "page_num" is optional and used for the pagination: it is a positive integer
      presenting the number of the current page
    - "nbr_items_per_page" is optional and used for the pagination: it is a
      positive integer presenting the number of items to display per page

    .. :quickref: list all Slurm job as formatted html
    """
    # Retrieve the parameters used to filter the jobs
    user_name = request.args.get("user_name", None)

    clusters_names = []
    raw_clusters_names = request.args.getlist("clusters_names")
    if len(raw_clusters_names) == 1:
        clusters_names = get_custom_array_from_request_args(raw_clusters_names[0])

    states = []
    raw_states = request.args.getlist("states")
    if len(raw_states) == 1:
        states = get_custom_array_from_request_args(raw_states[0])

    # Retrieve the pagination parameters
    pagination_page_num = request.args.get("page_num", type=int, default="1")
    pagination_nbr_items_per_page = request.args.get("nbr_items_per_page", type=int)
    # Use the pagination helper to define the number of element to skip, and the number of elements to display
    (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
        current_user.mila_email_username,
        pagination_page_num,
        pagination_nbr_items_per_page,
    )

    ###
    # Define the filters to select the jobs
    ###
    # Define the user filter
    user_name = request.args.get("user_name", None)
    if user_name is not None:
        f0 = {"cw.mila_email_username": user_name}
    else:
        f0 = {}

    # Define the filter related to the cluster on which the jobs run
    if len(clusters_names) > 0:
        f1 = {"slurm.cluster_name": {"$in": clusters_names}}
    else:
        f1 = {}  # Apply no filter for the clusters if no cluster has been provided

    # Define the filter related to the jobs' states
    if len(states) > 0:
        f2 = {"slurm.job_state": {"$in": states}}
    else:
        f2 = {}  # Apply no filter for the states if no state has been provided

    # Combine the filters
    filter = combine_all_mongodb_filters(f0, f1, f2)

    ###
    # Retrieve the jobs and display them
    ###
    # Retrieve the jobs, by applying the filters and the pagination
    LD_jobs = get_jobs(
        filter,
        nbr_skipped_items=nbr_skipped_items,
        nbr_items_to_display=nbr_items_to_display,
    )

    # TODO : You might want to stop doing the `infer_best_guess_for_username`
    # at some point to design something better. See CW-81.
    LD_jobs = [
        infer_best_guess_for_username(strip_artificial_fields_from_job(D_job))
        for D_job in LD_jobs
    ]

    # Display the HTML page
    return render_template_with_user_settings(
        "jobs_search.html",
        LD_jobs=LD_jobs,
        mila_email_username=current_user.mila_email_username,
        page_num=pagination_page_num,
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
    job_id = request.args.get("job_id", None)
    if job_id is None:
        return (
            render_template_with_user_settings(
                "error.html", error_msg=f"Missing argument job_id."
            ),
            400,
        )  # bad request
    f0 = get_filter_job_id(job_id)
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)

    LD_jobs = get_jobs(filter)

    if len(LD_jobs) == 0:
        return render_template_with_user_settings(
            "error.html", error_msg=f"Found no job with job_id {job_id}."
        )
    if len(LD_jobs) > 1:
        return render_template_with_user_settings(
            "error.html",
            error_msg=gettext(
                "Found %(len_LD_jobs) jobs with job_id %(job_id)."
            ).format(len_LD_jobs=len(LD_jobs), job_id=job_id),
        )  # Not sure what to do about these cases.

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)  # see CW-81

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
        job_id=job_id,
        mila_email_username=current_user.mila_email_username,
    )


# TODO : Everything below has not yet been ported to the new system.


@flask_api.route("/interactive")
@login_required
def route_interactive():
    """
    Not implemented.
    """
    return render_template_with_user_settings(
        "jobs_interactive.html",
        mila_email_username=current_user.mila_email_username,
    )
