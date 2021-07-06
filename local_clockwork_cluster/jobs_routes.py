from pprint import pprint
import re
import os
import json
import requests
import time
from collections import defaultdict

from mongo_client import get_mongo_client


# Use of "Markup" described there to avoid Flask escaping it when passing to a template.
# https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
from flask import render_template, request, send_file
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper
# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g


# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint
flask_api = Blueprint('jobs_flask_api', __name__)

from jobs_routes_helper import (strip_artificial_fields_from_job, get_job_state_totals, get_jobs, infer_best_guess_for_username)



@flask_api.route('/')
def route_index():
    return redirect("list/")


@flask_api.route('/list/', defaults={'mila_user_account': None})
@flask_api.route('/list/<mila_user_account>')
def route_list(mila_user_account:str):

    # filter out everything before the past 12 hours
    find_filter = {'submit_time': {'$gt': int(time.time() - 3600*12)}}

    if mila_user_account is None:
        LD_jobs = get_jobs(find_filter=find_filter)
    else:
        m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
        if not m:
            return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")
        LD_jobs = get_jobs(find_filter=dict( list(find_filter.items()) + list({'mila_user_account': mila_user_account}.items()) ))

    LD_jobs = [infer_best_guess_for_username(D_job) for D_job in LD_jobs]

    return render_template("jobs.html",
                            LD_jobs=LD_jobs)


@flask_api.route('/state_totals/', defaults={'mila_user_account': None})
@flask_api.route('/state_totals/<mila_user_account>')
def route_state_totals(mila_user_account):

    if mila_user_account is None:
        L_entries = get_jobs()
    else:
        m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
        if not m:
            return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")
        L_entries = get_jobs({'mila_user_account': mila_user_account})

    # TODO : Filter for recent jobs (except for the pending ones).
    DD_counts = get_job_state_totals(L_entries)

    # sort by the one that has the most RUNNING jobs first
    LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
    
    return render_template("jobs/job_state_totals.html",
                            LPD_job_state_totals=LPD_job_state_totals)


# @flask_api.route('/job_state_totals')
# def route_job_state_totals():
    
#     L_entries = get_jobs()
#     # TODO : Filter for recent jobs (except for the pending ones).
#     DD_counts = get_job_state_totals(L_entries)
   
#     # sort by the one that has the most RUNNING jobs first
#     LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
#     return render_template("jobs/job_state_totals.html",
#                             LPD_job_state_totals=LPD_job_state_totals)

@flask_api.route('/single_job/<job_id>')
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
    return render_template("single_job.html",
                            LP_single_job=LP_single_job,
                            job_id=job_id)


@flask_api.route('/api/list', methods=['POST'])
def route_api_list():
    """
    TODO : read the body of the request to have information about user, time, cluster, etc.

    Right now this is a bare minimum setup because we're working on jobs.html and clockwork.js
    at the same time.

    TODO : Think some more about the endpoints. Right now this is a good place
           for this endpoint, but some factoring should be done.
    """

    # filter out everything before the past 12 hours
    find_filter = {'submit_time': {'$gt': int(time.time() - 3600*12)}}

    LD_jobs = get_jobs(find_filter=find_filter)
    LD_jobs = [infer_best_guess_for_username(D_job) for D_job in LD_jobs]

    for D_job in LD_jobs:
        if "_id" in D_job:
            del D_job["_id"]

    # no need to jasonify it ourselves
    return jsonify(LD_jobs)