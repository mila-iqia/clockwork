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

from markupsafe import Markup
from flask import Flask, Response, url_for, request, redirect, make_response
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

from clockwork_web.core.clusters_helper import get_account_fields
from clockwork_web.core.utils import to_boolean, get_custom_array_from_request_args
from clockwork_web.core.users_helper import (
    render_template_with_user_settings,
    get_users,
)
from ..db import get_db

flask_api = Blueprint("admin", __name__)


def admin_access_required(f):
    """Checks for user admin rights."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.admin_access:
            return (
                render_template_with_user_settings(
                    "error.html",
                    error_msg=gettext("Authorization error."),
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
    """Admin home page"""
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


@flask_api.route("/users")
@login_required
@admin_access_required
def users():
    """Admin users page"""
    logging.info(
        f"clockwork browser route: /admin/users - current_user={current_user.mila_email_username}"
    )

    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Get users
    LD_users = sorted(get_users(), key=lambda user: user["mila_email_username"])

    # Get the different clusters fields
    D_clusters_usernames_fields = get_account_fields()

    return render_template_with_user_settings(
        "admin_users.html",
        mila_email_username=current_user.mila_email_username,
        previous_request_args=previous_request_args,
        LD_users=LD_users,
        D_clusters_usernames_fields = D_clusters_usernames_fields
    )


@flask_api.route("/user", methods=["POST", "GET"])
@login_required
@admin_access_required
def user():
    """
    Admin page to edit a specific user

    User to edit is passed as GEt parameter `username`

    Edited values (mila cluster ID and DRAC cluster ID)
    are passed as POST form.
    """
    logging.info(
        f"clockwork browser route: /admin/user - current_user={current_user.mila_email_username}"
    )

    # Initialize the request arguments (it is further transferred to the HTML)
    previous_request_args = {}

    # Get user
    mila_email_username = request.args.get("username", None)
    previous_request_args["username"] = mila_email_username

    if mila_email_username is None:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext("Missing argument username."),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )

    mc = get_db()
    users_collection = mc["users"]
    D_users = list(users_collection.find({"mila_email_username": mila_email_username}))

    if len(D_users) != 1:
        return (
            render_template_with_user_settings(
                "error.html",
                error_msg=gettext(f"Cannot find username: {mila_email_username}"),
                previous_request_args=previous_request_args,
            ),
            400,  # Bad Request
        )

    (D_user,) = D_users

    # Get the different clusters fields
    D_clusters_usernames_fields = get_account_fields()

    # Edition form
    user_edit_status = ""
    if request.method == "POST":
        # Handle edition form
        update_needed = False
        old_usernames = {}
        new_usernames = {}
        for cluster_username_field in D_clusters_usernames_fields:
            old_username = D_user[cluster_username_field]
            old_usernames[cluster_username_field] = old_username
            # old_mila_cluster_username = D_user["mila_cluster_username"]
            # old_cc_account_username = D_user["cc_account_username"]

            new_username = request.form[cluster_username_field].strip()
            if new_username:
                new_usernames[cluster_username_field] = new_username
                update_needed = True
                #new_mila_cluster_username = request.form["mila_cluster_username"].strip()
                #new_cc_account_username = request.form["cc_account_username"].strip()
            else:
                new_usernames[cluster_username_field] = old_username
            #if not new_mila_cluster_username:
            #    new_mila_cluster_username = old_mila_cluster_username

            #if not new_cc_account_username:
            #    new_cc_account_username = old_cc_account_username

        if update_needed:
            users_collection.update_one(
                {"mila_email_username": D_user["mila_email_username"]},
                {
                    "$set": new_usernames
                }
            )
            for cluster_username_field in D_clusters_usernames_fields:
                D_user[cluster_username_field] = new_usernames[cluster_username_field]
            user_edit_status = "User successfully updated."
        else:
            user_edit_status = "No change for this user."
        """
        if (
            new_mila_cluster_username != old_mila_cluster_username
            or new_cc_account_username != old_cc_account_username
        ):
            users_collection.update_one(
                {"mila_email_username": D_user["mila_email_username"]},
                {
                    "$set": {
                        "mila_cluster_username": new_mila_cluster_username,
                        "cc_account_username": new_cc_account_username,
                    }
                },
            )
            D_user["mila_cluster_username"] = new_mila_cluster_username
            D_user["cc_account_username"] = new_cc_account_username
            user_edit_status = "User successfully updated."
        else:
            user_edit_status = "No changes for this user."
        """

    return render_template_with_user_settings(
        "admin_user.html",
        mila_email_username=current_user.mila_email_username,
        previous_request_args=previous_request_args,
        D_user=D_user,
        user_edit_status=user_edit_status,
        D_clusters_usernames_fields=D_clusters_usernames_fields
    )
