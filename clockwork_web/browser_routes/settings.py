import re
import os
import json
import requests
import time
import secrets

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
from flask import request, send_file
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
from clockwork_web.core.users_helper import render_customized_template

@flask_api.route("/")
@fresh_login_required
def route_index():
    """

    .. :quickref: access the settings page as html
    """
    # Display the user's settings as HTML
    return render_customized_template(
        "settings.html",
        mila_email_username=current_user.mila_email_username,
        clockwork_api_key=current_user.clockwork_api_key,
        cc_account_update_key=current_user.cc_account_update_key,
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
@flask_api.route("/web/nbr_items_per_page/set")
@login_required
def route_set_nbr_items_per_page():
    """
    Set a new value to the preferred number of items to display per page for the
    current user.

    .. :quickref: set the number of items to display per page in the current
                  user's settings
    """
    # Retrieve the preferred number of items to display per page (ie the number
    # to store in the settings), called nbr_items_per_page
    nbr_items_per_page = request.args.get("nbr_items_per_page", type=int)

    # Check if nbr_items_per_page exists
    if nbr_items_per_page:
        # Check if nbr_items_per_page is a positive integer
        if type(nbr_items_per_page) == int and nbr_items_per_page > 0:
            # If it is, update this number in the current user's settings and
            # retrieve the status code and status message associated to this
            # operation
            (
                status_code,
                status_message,
            ) = current_user.settings_nbr_items_per_page_set(nbr_items_per_page)

            if status_code == 200:
                # If a success has been return, redirect to the settings page
                return redirect("/settings")
            else:
                # Otherwise, return an error
                return (
                    render_customized_template("error.html", error_msg=status_message),
                    status_code,
                )
        else:
            # Otherwise, return a Bad Request error and redirect to the error page
            return (
                render_customized_template(
                    "error.html",
                    error_msg=f"Wrong number of items to display per page provided to be set.",
                ),
                400,  # Bad Request
            )
    else:
        # If nbr_items_per_page does not exist, return Bad Request
        return (
            render_customized_template(
                "error.html",
                error_msg=f"Missing argument, or wrong format: nbr_items_per_page.",
            ),
            400,  # Bad Request
        )


@flask_api.route("/web/dark_mode/set")
@login_required
def route_set_dark_mode():
    """
    Enable the dark mode web setting for the current user.

    .. :quickref: enable the dark mode for the current user
    """
    # Set the dark mode value to True in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_dark_mode_enable()

    if status_code == 200:
        # If a success has been returned
        return {}  # TODO: I'm not sure this is the correct way to do this
    else:
        # Otherwise, return an error
        return (render_customized_template("error.html", error_msg=status_message), status_code)


@flask_api.route("/web/dark_mode/unset")
@login_required
def route_unset_dark_mode():
    """
    Disable the dark mode web setting for the current user.

    .. :quickref: disable the dark mode for the current user
    """
    # Set the dark mode value to False in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_dark_mode_disable()

    if status_code == 200:
        # If a success has been returned
        return {}  # TODO: I'm not sure this is the correct way to do this
    else:
        # Otherwise, return an error
        return (render_customized_template("error.html", error_msg=status_message), status_code)
