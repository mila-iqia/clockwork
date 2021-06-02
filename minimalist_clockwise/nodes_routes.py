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
flask_api = Blueprint('nodes_flask_api', __name__)


@flask_api.route('/')
def route_index():
    mc_db = get_mongo_client()['slurm']
    L_entries = list(mc_db["nodes_collection"].find())
    # let's not always process them in the same order
    #L_entries = list(sorted(L, key=lambda e: e['title']))

    return render_template("nodes/plain/home.html",
                            L_entries=L_entries)
