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
from flask import g, session

from flask_login import current_user, fresh_login_required, login_required
from flask_babel import gettext

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

flask_api = Blueprint("settings", __name__)

from clockwork_web.user import User
from clockwork_web.config import register_config, get_config, string as valid_string

register_config("translation.available_languages", valid_string)

from clockwork_web.core.users_helper import render_template_with_user_settings
from clockwork_web.core.jobs_helper import get_jobs_properties_list_per_page


@flask_api.route("/")
@fresh_login_required
def route_index():
    """

    .. :quickref: access the settings page as html
    """
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Display the user's settings as HTML
    return render_template_with_user_settings(
        "settings.html",
        mila_email_username=current_user.mila_email_username,
        clockwork_api_key=current_user.clockwork_api_key,
        cc_account_update_key=current_user.cc_account_update_key,
        previous_request_args=previous_request_args,
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
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Retrieve the preferred number of items to display per page (ie the number
    # to store in the settings), called nbr_items_per_page
    nbr_items_per_page = request.args.get("nbr_items_per_page", type=int)
    previous_request_args["nbr_items_per_page"] = nbr_items_per_page

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
                    render_template_with_user_settings(
                        "error.html",
                        error_msg=status_message,
                        previous_request_args=previous_request_args,
                    ),
                    status_code,
                )
        else:
            # Otherwise, return a Bad Request error and redirect to the error page
            return (
                render_template_with_user_settings(
                    "error.html",
                    error_msg=gettext(
                        "Invalid choice for number of items to display per page."
                    ),
                    previous_request_args=previous_request_args,
                ),
                400,  # Bad Request
            )
    else:
        # If nbr_items_per_page does not exist, return Bad Request
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext(
                    "Missing argument, or wrong format: nbr_items_per_page."
                ),
                previous_request_args=previous_request_args,
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
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Set the dark mode value to True in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_dark_mode_enable()

    if status_code == 200:
        # If a success has been returned
        return {}  # TODO: I'm not sure this is the correct way to do this
    else:
        # Otherwise, return an error
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=status_message,
                previous_request_args=previous_request_args,
            ),
            status_code,
        )


@flask_api.route("/web/dark_mode/unset")
@login_required
def route_unset_dark_mode():
    """
    Disable the dark mode web setting for the current user.

    .. :quickref: disable the dark mode for the current user
    """
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Set the dark mode value to False in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_dark_mode_disable()

    if status_code == 200:
        # If a success has been returned
        return {}  # TODO: I'm not sure this is the correct way to do this
    else:
        # Otherwise, return an error
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=status_message,
                previous_request_args=previous_request_args,
            ),
            status_code,
        )


@flask_api.route("/web/column/set")
@login_required
def route_set_column_display():
    """
    Set to true the fact that a specific column is shown on the web page "dashboard"
    or "jobs list" (regarding the value of the parameter "page").

    .. :quickref: enable the display of a job element on the dashboard or on the jobs list
    """
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Retrieve the column and page names provided in the request
    column_name = request.args.get("column", type=str)
    previous_request_args["column"] = column_name

    page_name = request.args.get("page", type=str)
    previous_request_args["page"] = page_name

    # Check if the tuple (page_name, column_name) is consistent
    jobs_properties_list_per_page = get_jobs_properties_list_per_page()
    # - Check the page name
    if page_name not in jobs_properties_list_per_page:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("The provided page name is unexpected."),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )
    # - Check the column name
    if column_name not in jobs_properties_list_per_page[page_name]:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext(
                    "The provided column name is unexpected for this page."
                ),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )

    # Set the column display value to True in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_column_display_enable(
        page_name, column_name
    )

    if status_code == 200:
        # If a success has been returned
        return {}
    else:
        # Otherwise, return an error
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=status_message,
                previous_request_args=previous_request_args,
            ),
            status_code,
        )


@flask_api.route("/web/column/unset")
@login_required
def route_unset_column_display():
    """
    Set to false the fact that a specific column is shown on the web page "dashboard"
    or "jobs list" (regarding the value of the parameter "page").

    .. :quickref: enable the display of a job element on the dashboard or on the jobs list
    """
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Retrieve the column and page names provided in the request
    column_name = request.args.get("column", type=str)
    previous_request_args["column"] = column_name

    page_name = request.args.get("page", type=str)
    previous_request_args["page"] = page_name

    # Check if the tuple (page_name, column_name) is consistent
    jobs_properties_list_per_page = get_jobs_properties_list_per_page()
    # - Check the page name
    if page_name not in jobs_properties_list_per_page:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("The provided page name is unexpected."),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )
    # - Check the column name
    if column_name not in jobs_properties_list_per_page[page_name]:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext(
                    "The provided column name is unexpected for this page."
                ),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )

    # Set the column display value to True in the current user's web settings and
    # retrieve the status code and status message associated to the operation
    (status_code, status_message) = current_user.settings_column_display_disable(
        page_name, column_name
    )

    if status_code == 200:
        # If a success has been returned
        return {}
    else:
        # Otherwise, return an error
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=status_message,
                previous_request_args=previous_request_args,
            ),
            status_code,
        )


@flask_api.route("/web/language/set")
@login_required
def route_set_language():
    """
    Set a new preferred language to display the website for the current authenticated user.

    .. :quickref: update the preferred language in the current user's settings
    """
    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Retrieve the preferred language to store in the settings
    language = request.args.get("language", type=str)
    previous_request_args["language"] = language

    # Check if language exists
    if language:
        # Check if the language is supported
        if language in get_config("translation.available_languages"):
            # If the language is known, update the preferred language of the
            # current user and retrieve the status code and status message
            # associated to this operation
            (
                status_code,
                status_message,
            ) = current_user.settings_language_set(language)

            if status_code == 200:
                # If a success has been return, redirect to the home page
                return redirect("/")
            else:
                # Otherwise, return an error
                return (
                    render_template_with_user_settings(
                        "error.html",
                        error_msg=status_message,
                        previous_request_args=previous_request_args,
                    ),
                    status_code,
                )

        else:
            # Otherwise, return a Bad Request error and redirect to the error page
            return (
                render_template_with_user_settings(
                    "error.html",
                    error_msg=gettext("The requested language is unknown."),
                    previous_request_args=previous_request_args,
                ),
                400,  # Bad Request
            )
    else:
        # If the language argument is not provided or presents a unexpected type,
        # return Bad Request
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("Missing argument, or wrong format: language."),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )
