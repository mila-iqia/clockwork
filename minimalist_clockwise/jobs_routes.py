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

# We'll have to do something about that setup to avoid hardcoding these values here.
D_mongo_config = {"hostname":"deepgroove.local", "port":27017, "username":"mongoadmin", "password":"secret_password_okay"}

def strip_artificial_fields_from_job(D_job):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id", "grafana_helpers"]
    return dict( (k, v) for (k, v) in D_job.items() if k not in fields_to_remove)


@flask_api.route('/')
def route_index():
    mc = get_mongo_client(D_mongo_config)
    mc_db = mc['slurm']
    L_entries = list(mc_db["jobs"].find())
    # let's not always process them in the same order
    #L_entries = list(sorted(L, key=lambda e: e['title']))

    return render_template("jobs/jobs.html",
                            L_entries=L_entries)

@flask_api.route('/<mila_user_account>')
def route_arg_mila_user_account(mila_user_account:str):

    m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
    if not m:
        return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")

    mc = get_mongo_client(D_mongo_config)
    mc_db = mc['slurm']
    L_entries = list(mc_db["jobs"].find({'mila_user_account': mila_user_account}))
    # let's not always process them in the same order
    #L_entries = list(sorted(L, key=lambda e: e['title']))

    return render_template("jobs/jobs.html",
                            L_entries=L_entries)

# Not super useful by itself.
@flask_api.route('/job_state_totals/<mila_user_account>')
def route_job_state_totals_mila_user_account(mila_user_account):

    m = re.match(r"^[a-zA-Z\.\d\-]+$", mila_user_account)
    if not m:
        return render_template("error.html", error_msg="mila_user_account specific contains invalid characters")

    mc = get_mongo_client(D_mongo_config)
    mc_db = mc['slurm']
    L_entries = list(mc_db["jobs"].find({'mila_user_account': mila_user_account}))

    # TODO : Filter for recent jobs (except for the pending ones).

    DD_counts = get_job_state_totals(L_entries)
    pprint(DD_counts)

    # sort by the one that has the most RUNNING jobs first
    LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
    
    return render_template("jobs/job_state_totals.html",
                            LPD_job_state_totals=LPD_job_state_totals)


@flask_api.route('/job_state_totals')
def route_job_state_totals():
    mc = get_mongo_client(D_mongo_config)
    mc_db = mc['slurm']
    L_entries = list(mc_db["jobs"].find())

    # TODO : Filter for recent jobs (except for the pending ones).

    DD_counts = get_job_state_totals(L_entries)
    pprint(DD_counts)

    # sort by the one that has the most RUNNING jobs first
    LPD_job_state_totals = sorted(DD_counts.items(), key=lambda e: -e[1]["RUNNING"])
    
    return render_template("jobs/job_state_totals.html",
                            LPD_job_state_totals=LPD_job_state_totals)

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


@flask_api.route('/single_job/<job_id>')
def route_single_job_p_job_id(job_id):

    m = re.match(r"^[\d]+$", job_id)
    if not m:
        return render_template("error.html", error_msg="job_id contains invalid characters")

    mc = get_mongo_client(D_mongo_config)
    mc_db = mc['slurm']
    L_entries = list(mc_db["jobs"].find({'job_id': int(job_id)}))

    if len(L_entries) == 0:
        return render_template("error.html", error_msg=f"Found no job with job_id {job_id}.")
    if len(L_entries) > 1:
        return render_template("error.html", error_msg=f"Found {len(L_entries)} jobs with job_id {job_id}. Not sure what to do about these cases.")

    D_job = strip_artificial_fields_from_job(L_entries[0])

    # let's sort alphabetically by keys
    LP_single_job = list(sorted(D_job.items(), key=lambda e: e[0]))
    return render_template("jobs/single_job.html",
                            LP_single_job=LP_single_job,
                            job_id=job_id)