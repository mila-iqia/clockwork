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
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
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

    state = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=20))

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "callback",
        scope=["openid", "email", "profile"],
        state=state
    )
    session['state'] = state
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

    state = session['state']

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
        return render_template(
            "error.html",
            error_msg="User email not available or not verified by Google.",
        )

    user = User.get(unique_id)
    # The first time around, if user is None, it's either
    # because of a corrupted database (should not happen, worth investigating),
    # or because it simply was never created.
    if user is None:
        success, error_msg = User.add_to_database(
            unique_id, users_name, users_email, picture
        )
        if not success:
            return render_template(
                "error.html",
                error_msg=f"Failed to add a user to the database. {error_msg}",
            )
        else:
            # We successfully added the user to the database,
            # so we should be able to retrieve it now.
            user = User.get(unique_id)
            if user is None:
                # If we still have a `None`, then it means that we really have an error.
                # Again, if we had a database corruption, then this should have been
                # detected earlier, but let's test anyway.
                return render_template(
                    "error.html",
                    error_msg="We tried to create an account for {users_email} but it failed.",
                )

    # At this point in the code, the user cannot possibly be `None`.

    if user.status != "enabled":
        return render_template(
            "error.html",
            error_msg="The user retrieved does not have its status as 'enabled'.",
        )
        # return f"The user retrieved does not have its status as 'enabled'.", 400

    login_user(user)
    print(
        f"called login_user(user) for user with email {user.email}, user.is_authenticated is {user.is_authenticated}"
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


"""
When logins are disabled, we add the route /login/new_fake_user in order to be able
to login easily to test out functionality locally.

To be more precise, this piece of code is useful not when running pytest,
but when poking around in the browser, with the web server running locally
(thus being unable to test using https).

Since the "LOGIN_DISABLED" environment variable is already being used,
we might as well use it.
"""

if os.environ.get("LOGIN_DISABLED", "False") in ["True", "true", "1"]:

    @flask_api.route("/new_fake_user")
    def route_new_fake_user():
        """
        Login as a fake user that's not present in the database yet.
        This will cause the creation of that user entry in the database.
        """
        unique_id = str(random.randint(0, 1e12))
        user = User.get(unique_id)
        if user is None:
            User.add_to_database(
                unique_id,
                "Fake User %s" % unique_id,
                "fake_user_%s@mila.quebec" % unique_id,
                "",
            )
        user = User.get(unique_id)
        assert (
            user is not None
        ), "Failed to create a fake user with route /login/new_fake_user."
        login_user(user)
        return redirect(url_for("index"))

    # @flask_api.route("/fake_user")
    # def route_fake_user():
    #     """
    #     This pertains to CW-90 which is not yet done.
    #
    #     Login as a fake user defined in the file "fake_data.json".
    #     We hardcoded here its user id. This corresponds to the user
    #     defined by
    #     {
    #         "google_suite": {
    #             "id": "4000",
    #             "name": "google_suite_user00",
    #             "email": "student00@mila.quebec",
    #             "profile_pic": ""},
    #         "cw": {
    #             "status": "enabled",
    #             "clockwork_api_key": "000aaa00"
    #         },
    #         "accounts_on_clusters": {
    #             "mila": {...},
    #             "beluga": {...},
    #             "graham": {...},
    #             "cedar": {...},
    #             "narval": {...}
    #         }
    #     }
    #     """
    #     unique_id = "4000"
    #     user = User.get(unique_id)
    #     assert user is not None
    #     login_user(user)
    #     return redirect(url_for("index"))
