import re
import os
import json
import requests
import time
import secrets

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
from flask import render_template, request, send_file
from flask import jsonify

# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g

from flask_login import (
    current_user,
    fresh_login_required,
)

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

flask_api = Blueprint("settings", __name__)

from clockwork_web.user import User


@flask_api.route("/")
@fresh_login_required
def route_index():
    """

    .. :quickref: access the settings page as html
    """
    return render_template(
        "settings.html",
        mila_email_username=current_user.email.split("@")[0],
        clockwork_api_key=current_user.clockwork_api_key,
    )


@flask_api.route("/new_key")
@fresh_login_required
def route_key():
    """
    Generate a new API key, invalidating the old one.
    """
    current_user.clockwork_api_key = secrets.token_hex(32)
    current_user.update()
    return redirect("/settings/")
