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

from jobs_routes_helper import (strip_artificial_fields_from_job, get_job_state_totals, get_jobs)

@flask_api.route('/')
def route_index():
    return redirect("list/")

@flask_api.route('/list/', defaults={'mila_user_account': None})
@flask_api.route('/list/<mila_user_account>')
def route_list(mila_user_account:str):

    if mila_user_account is None:
        L_entries = get_jobs()
    else:
        m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
        if not m:
            return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")
        L_entries = get_jobs({'mila_user_account': mila_user_account})

    return render_template("jobs/jobs.html",
                            L_entries=L_entries)

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

@flask_api.route('/single_job')
def route_single_job():
    job_id = request.args.get('job_id', default=None, type=int)
    want_plain = request.args.get('want_plain', default=0, type=int) == 1
    cluster_name = request.args.get('cluster_name', default=None, type=str)

    filter_find = {}

    if job_id is None:
        return render_template("error.html", error_msg="Missing job_id. Pass it with   jobs/single_job?job_id=12345678")
    else:
        filter_find['job_id'] = job_id

    if cluster_name is not None:
        if cluster_name not in ["mila", "beluga", "graham", "cedar"]:
            return render_template("error.html", error_msg=f"Invalid cluster_name argument : {cluster_name}")
        else:
            filter_find['cluster_name'] = cluster_name

    LD_jobs = get_jobs(filter_find)

    if len(LD_jobs) == 0:
        return render_template("error.html", error_msg=f"Found no job with job_id {job_id}.")
    if len(LD_jobs) > 1:
        return render_template("error.html", error_msg=f"Found {len(LD_jobs)} jobs with job_id {job_id}. Not sure what to do about these cases.")

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    # let's sort alphabetically by keys
    LP_single_job = list(sorted(D_job.items(), key=lambda e: e[0]))
    if want_plain == 1:
        return render_template("jobs/single_job_plain.html",
                                LP_single_job=LP_single_job,
                                job_id=job_id)
    else:
        return render_template("jobs/single_job.html",
                                LP_single_job=LP_single_job,
                                job_id=job_id)