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

from flask_login import current_user, fresh_login_required, login_required

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
    # Display the user's settings as HTML
    return render_template(
        "settings.html",
        mila_email_username=current_user.mila_email_username,
        clockwork_api_key=current_user.clockwork_api_key,
        cc_account_update_key=current_user.cc_account_update_key,
        web_settings=current_user.web_settings,
    )


@flask_api.route("/new_key")
@fresh_login_required
def route_key():
    """
    Generate a new API key, invalidating the old one.
    """
    current_user.new_api_key()
    return redirect("/settings/")


@flask_api.route("/new_update_key")
@fresh_login_required
def route_update_key():
    """
    Generate a new account update key.
    """
    current_user.new_update_key()
    return redirect("/settings/")


###
#   This section is related to the web settings of the current user
###


@flask_api.route("/web/dark_mode/set")
@login_required
def route_set_dark_mode():
    """
    Enable the dark mode web setting for the current user.
    """
    current_user.settings_dark_mode_enable()
    return (
        {}
    )  # TODO: I'm not sure this is the correct way to do this


@flask_api.route("/web/dark_mode/unset")
@login_required
def route_unset_dark_mode():
    """
    Disable the dark mode web setting for the current user.
    """
    current_user.settings_dark_mode_disable()
    return (
        {}
    )  # TODO: I'm not sure this is the correct way to do this
