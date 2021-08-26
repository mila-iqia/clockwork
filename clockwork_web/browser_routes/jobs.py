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
from flask import render_template, request, send_file
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper
# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g

from flask_login import (
    current_user,
    login_required,
)

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint
flask_api = Blueprint('jobs', __name__)

from clockwork_web.core.jobs_helper import (
    get_filter_user,
    get_filter_time,
    get_filter_cluster_name,
    get_filter_job_id,
    combine_all_mongodb_filters,
    strip_artificial_fields_from_job,
    get_mongodb_filter_from_query_filter,
    get_jobs,
    infer_best_guess_for_username)
from clockwork_web.core.common import get_filter_from_request_args, get_mila_email_username


@flask_api.route('/')
@login_required
def route_index():
    """
    Not implemented, but this will be the new name for the jobs.html with interactions.
    """
    return redirect("interactive")

@flask_api.route('/list')
@login_required
def route_list():
    """
    Can take optional args "cluster_name", "user", "time".
    
    "user" refers to any of the three alternatives to identify a user,
    and it will many any of them.
    "time" refers to how many seconds to go back in time to list jobs.
    """

    f0 = get_filter_user(request.args.get("user", None))
    
    time1 = request.args.get('time', None)
    try:
        f1 = get_filter_time(time1)
    except Exception as inst:
        print(inst)
        return render_template("error.html", error_msg=f"Field 'time' cannot be cast as a valid integer: {time1}."), 400  # bad request

    filter = combine_all_mongodb_filters(f0, f1)

    # pprint(filter)
    LD_jobs = get_jobs( filter )

    LD_jobs = [infer_best_guess_for_username(strip_artificial_fields_from_job(D_job))
                 for D_job in LD_jobs]

    for D_job in LD_jobs:
        if D_job is None:
            print("OMG, D_job is None!" * 100)
            # quit()

    return render_template("jobs.html", LD_jobs=LD_jobs, mila_email_username=get_mila_email_username())


@flask_api.route('/one')
@login_required
def route_one():
    """
    Takes args "cluster_name", "job_id".
    This can work with only "job_id" if it's unique,
    but otherwise it might require specifying the cluster name.
    """
    job_id = request.args.get("job_id", None)
    if job_id is None:
        return render_template("error.html", error_msg=f"Missing argument job_id."),  400  # bad request
    f0 = get_filter_job_id(job_id)
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)

    LD_jobs = get_jobs(filter)

    if len(LD_jobs) == 0:
        return render_template("error.html", error_msg=f"Found no job with job_id {job_id}.")
    if len(LD_jobs) > 1:
        return render_template("error.html", error_msg=f"Found {len(LD_jobs)} jobs with job_id {job_id}. Not sure what to do about these cases.")

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)

    # let's sort alphabetically by keys
    LP_single_job = list(sorted(D_job.items(), key=lambda e: e[0]))

    return render_template("single_job.html",
                            LP_single_job=LP_single_job,
                            job_id=job_id,
                            mila_email_username=get_mila_email_username())




# TODO : Everything below has not yet been ported to the new system.

@flask_api.route('/interactive')
@login_required
def route_interactive():
    """
    Not implemented.
    """
    return render_template("jobs_interactive.html", mila_email_username=get_mila_email_username())

@flask_api.route('/single_job/<job_id>')
@login_required
def route_single_job_p_job_id(job_id):

    m = re.match(r"^[\d]+$", job_id)
    if not m:
        return render_template("error.html", error_msg="job_id contains invalid characters")

    LD_jobs = get_jobs({'job_id': int(job_id)})

    if len(LD_jobs) == 0:
        return render_template("error.html", error_msg=f"Found no job with job_id {job_id}.")
    if len(LD_jobs) > 1:
        return render_template("error.html", error_msg=f"Found {len(LD_jobs)} jobs with job_id {job_id}. Not sure what to do about these cases.")

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)

    # let's sort alphabetically by keys
    LP_single_job = list(sorted(D_job.items(), key=lambda e: e[0]))

    # When running tests against routes protected by login (under normal circumstances),
    # `current_user` is not specified, so retrieving the email would lead to errors.
    if hasattr(current_user, "email"):
        mila_email_username = current_user.email.split("@")[0]
    else:
        mila_email_username = None

    return render_template("single_job.html",
                            LP_single_job=LP_single_job,
                            job_id=job_id,
                            mila_email_username=mila_email_username)