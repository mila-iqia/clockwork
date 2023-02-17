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

flask_api = Blueprint("admin", __name__)


@flask_api.route("/panel")
# TODO : Add a decorator to check that the user is an admin.
@login_required
def route_index():
    """ """
    return render_template_with_user_settings(
        "jobs_search.html",
        mila_email_username=current_user.mila_email_username,
    )
