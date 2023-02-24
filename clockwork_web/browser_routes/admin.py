from pprint import pprint
import re
import os
import json
import requests
import time
import logging
from collections import defaultdict
from functools import wraps

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


def admin_access_required(f):
    """Checks for user admin rights."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.admin_access:
            return (
                render_template_with_user_settings(
                    "error.html",
                    error_msg=f"Authorization error.",
                    previous_request_args={},
                ),
                403,  # access rights error
            )

        return f(*args, **kwargs)

    return decorated


@flask_api.route("/panel")
@login_required
@admin_access_required
def panel():
    """ """
    logging.info(
        f"clockwork browser route: /admin/panel - current_user={current_user.mila_email_username}"
    )

    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    return render_template_with_user_settings(
        "admin_panel.html",
        mila_email_username=current_user.mila_email_username,
        previous_request_args=previous_request_args,
    )
