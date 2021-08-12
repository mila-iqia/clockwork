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
flask_api = Blueprint('nodes', __name__)

from clockwork_web.core.nodes_helper import get_nodes
from clockwork_web.core.common import get_filter_from_request_args

def get_mila_email_username():
    # When running tests against routes protected by login (under normal circumstances),
    # `current_user` is not specified, so retrieving the email would lead to errors.
    if hasattr(current_user, "email"):
        return current_user.email.split("@")[0]
    else:
        return None


@flask_api.route('/')
@login_required
def route_index():
    """
    Can take optional args "cluster_name" and "name",
    where "name" refers to the host name.
    """
    filter = get_filter_from_request_args(["cluster_name", "name"])
    LD_nodes = get_nodes(filter)
    return render_template("nodes.html", LD_nodes=LD_nodes, mila_email_username=get_mila_email_username())
