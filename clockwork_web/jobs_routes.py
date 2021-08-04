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

# from web_server import jobs_routes_helper
from .jobs_routes_helper import (
    strip_artificial_fields_from_job,
    get_job_state_totals,
    get_mongodb_filter_from_query_filter,
    get_jobs,
    infer_best_guess_for_username)

@flask_api.route('/')
@login_required
def route_index():
    return redirect("list")


# @flask_api.route('/list/', defaults={'mila_user_account': None})
# @flask_api.route('/list/<mila_user_account>')
@flask_api.route('/list')
@login_required
def route_list():
    """
    This is the main route that's going to be used.
    """
    # We can work some other time at adding the back the username argument.
    # This could be set as the default value in the option box in jobs.html.
    # Let's leave it out for now.

    mila_email_username = current_user.email.split("@")[0]
    return render_template("jobs.html", mila_email_username=mila_email_username)


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

    mila_email_username = current_user.email.split("@")[0]
    return render_template("single_job.html",
                            LP_single_job=LP_single_job,
                            job_id=job_id,
                            mila_email_username=mila_email_username)


@flask_api.route('/api/list', methods=['POST'])
def route_api_list():
    """
    This is the endpoint that serves jobs.html making requests.
    It provides all the information.

    TODO : Add the authentication code in here. This consists of
           the route wrapper. We have done this in some other project,
           so it'll be a question of porting that code to this project.
           Do we really trust that a .get_json() won't cause problems
           with maliciously-formatted json? I imagine so, but it's worth
           some investigation. At least it's not the default python "json" library.

    TODO : Think some more about the endpoints. Right now this is a good place
           for this endpoint, but some factoring should be done.
    """

    try:
        body = request.get_json()
    except Exception as inst:
        return (f"Failed to retrieve json data in request.\n"
                f"type(inst) is {type(inst)}\n"
                f"{inst}\n"), 200

    if body is None:
        return "request.get_json() returns None.", 200
    elif not isinstance(body, dict):
        return "request.get_json() did not return a dict.", 200
    elif 'query_filter' not in body:
        return "Missing field 'query_filter' in request body.", 200

    query_filter = body['query_filter']
    # `query_filter` looks like this
    #     {'time': 3600, 'user': 'all'}}
    pprint(query_filter)

    # Sanitize a little by removing spaces.
    # (This can occur when we type usernames from the web site.)
    if 'user' in query_filter:
        query_filter['user'] = query_filter['user'].replace(" ", "")
    if 'time' in query_filter:
        try:
            query_filter['time'] = int(query_filter['time'])
        except:
            return f"Field 'time' cannot be cast as a valid integer: {query_filter['time']}.", 200

    mongodb_filter = get_mongodb_filter_from_query_filter(query_filter)
    # filter out everything before the past 12 hours
    # mongodb_filter = {'submit_time': {'$gt': int(time.time() - 3600*12)}}

    pprint(mongodb_filter)

    LD_jobs = get_jobs(mongodb_filter=mongodb_filter)
    print(len(LD_jobs))

    LD_jobs = [infer_best_guess_for_username(D_job) for D_job in LD_jobs]

    # Strip out the "_id" extra field added by mongodb.
    # It is not json-serializable, and it's also meaningless
    # in terms of the rest of this application.
    for D_job in LD_jobs:
        if "_id" in D_job:
            del D_job["_id"]

    # no need to jsonify it ourselves
    return jsonify(LD_jobs)






#########################
#####  The junkyard #####
#########################

# @flask_api.route('/state_totals/', defaults={'mila_user_account': None})
# @flask_api.route('/state_totals/<mila_user_account>')
# def route_state_totals(mila_user_account):

#     if mila_user_account is None:
#         L_entries = get_jobs()
#     else:
#         m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
#         if not m:
#             return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")
#         L_entries = get_jobs({'mila_user_account': mila_user_account})

#     # TODO : Filter for recent jobs (except for the pending ones).
#     DD_counts = get_job_state_totals(L_entries)

#     # sort by the one that has the most RUNNING jobs first
#     LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
    
#     return render_template("jobs/job_state_totals.html",
#                             LPD_job_state_totals=LPD_job_state_totals)


# @flask_api.route('/job_state_totals')
# def route_job_state_totals():
    
#     L_entries = get_jobs()
#     # TODO : Filter for recent jobs (except for the pending ones).
#     DD_counts = get_job_state_totals(L_entries)
   
#     # sort by the one that has the most RUNNING jobs first
#     LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
#     return render_template("jobs/job_state_totals.html",
#                             LPD_job_state_totals=LPD_job_state_totals)
