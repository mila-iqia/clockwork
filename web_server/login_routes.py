"""

TODO : Whatever you did with /logout, now you'll be doing with /login/logout
       if you set up your routes like that.

TODO : For the whole REST API thing, you should think about what's written here:
        https://flask-login.readthedocs.io/en/latest/
        Custom Login using Request Loader

"""

from logging import error
import os
import json

from flask import Flask, redirect, render_template, request, url_for

from oauthlib.oauth2 import WebApplicationClient
import requests

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from user import User


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)


# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint
flask_api = Blueprint('login_routes', __name__)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# TODO : Does this go here? Is it just needed in one function only?
# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)
#############################################



@flask_api.route("/")
def login_routes_index():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "callback",
        scope=["openid", "email", "profile"],  # 2021-07-15 we removed "openid" from list because we set up OAuth without asking for "openid"
    )
    return redirect(request_uri)


@flask_api.route("/callback")
def login_routes_callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return render_template("error.html", error_msg="User email not available or not verified by Google.")
    
    user = User.get(unique_id)
    # The first time around, if user is None, it's either
    # because of a corrupted database (should not happen, worth investigating),
    # or because it simply was never created.
    if user is None:
        success, error_msg = User.add_to_database(unique_id, users_name, users_email, picture)
        if not success:
            return render_template("error.html", error_msg=f"Failed to add a user to the database. {error_msg}")
        else:
            # We successfully added the user to the database,
            # so we should be able to retrieve it now.
            user = User.get(unique_id)
            if user is None:
                # If we still have a `None`, then it means that we really have an error.
                # Again, if we had a database corruption, then this should have been
                # detected earlier, but let's test anyway.
                return render_template("error.html", error_msg="We tried to create an account for {users_email} but it failed.")

    # At this point in the code, the user cannot possibly be `None`.

    if user.status != "enabled":
        return render_template("error.html", error_msg="The user retrieved does not have its status as 'enabled'.")
        # return f"The user retrieved does not have its status as 'enabled'.", 400

    login_user(user)
    print(  f"called login_user(user) for user with email {user.email}, user.is_authenticated is {user.is_authenticated}")
    # Send user back to homepage
    return redirect("/")


@flask_api.route("/logout")
@login_required
def login_routes_logout():
    logout_user()
    redirect("/")
    # return redirect(url_for("index"))

