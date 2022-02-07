"""
This code handles the OAuth part of the server.
It does involve some cargo-cult code from online tutorials
about using Google's OAuth 2.0 service.

The other source of complexity is that testing a Flask
app requires bypassing the authentication in some places,
and having a proper user authenticated at other places.
This is feasible, but it leads to code that might be
a little more convoluted than otherwise.

For the developers, this is a useful resource:
    https://flask-login.readthedocs.io/en/latest/
    Custom Login using Request Loader
"""

from logging import error
import os
import json
import random
import string

from flask import Flask, redirect, render_template, request, url_for, session

from oauthlib.oauth2 import WebApplicationClient
import requests

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from .user import User


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

flask_api = Blueprint("login", __name__)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# TODO : Does this go here? Is it just needed in one function only?
# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)
#############################################


@flask_api.route("/")
def route_index():
    """Browsing to this starts the authentication dance.

    We prepare the necessary components to have the user be
    directed to the Google OAuth services, which also includes
    an address (the callback) that they'll use to return to us afterwards.

    Returns: Redirects the browser to Google's authentication server.
    """
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    state = "".join(
        random.choices(
            string.ascii_lowercase + string.ascii_uppercase + string.digits, k=20
        )
    )

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "callback",
        scope=["openid", "email", "profile"],
        state=state,
    )
    session["state"] = state
    return redirect(request_uri)


@flask_api.route("/callback")
def route_callback():
    """Browser destination after authentication with Google.

    After having talked with Google for the authentication,
    the user is told to browse back to this address, but with
    a code in hand to be used by us to retrieve the access token.
    With that code, we can finish the conversation with Google.

    Note that we don't save any of that server-side because
    we are not going to do anything on behalf of the users on Google.
    We just want to identify them and get basic information.

    Returns: Redirects the browser to the index of the page afterwards,
    which will now act differently facing an authenticated user.
    """

    state = session["state"]

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
        state=state,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(token_response.text)

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        users_email = userinfo["email"]
    else:
        return render_template(
            "error.html",
            error_msg="User email not available or not verified by Google.",
        )

    if not users_email.endswith("@mila.quebec"):
        return render_template(
            "error.html", error_msg="We accept only accounts from @mila.quebec"
        )

    user = User.get(users_email)

    if user is None:
        return render_template(
            "error.html",
            error_msg=f"User not available, contact support for more information",
        )
    # At this point in the code, the user cannot possibly be `None`.

    if user.status != "enabled":
        return render_template(
            "error.html",
            error_msg="The user retrieved does not have its status as 'enabled'.",
        )

    login_user(user)
    print(
        f"called login_user(user) for user with email {user.mila_email_username}, user.is_authenticated is {user.is_authenticated()}"
    )
    # Send user back to homepage
    return redirect(url_for("index"))


@flask_api.route("/logout")
@login_required
def route_logout():
    """Logs out the user when browsing to this address.

    Everything happens through the `flask_login` module,
    and we just need to call `logout_user()`.
    """
    logout_user()
    return redirect(url_for("index"))
