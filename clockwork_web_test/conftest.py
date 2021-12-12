"""
This is a special file that pytest will find first.
"""

import base64
import os
import json
from flask.globals import current_app

from flask_login import login_user, logout_user

import pytest

import clockwork_web
from clockwork_web.server_app import create_app
from clockwork_web.db import get_db, init_db
from clockwork_web.user import User

from test_common.fake_data import fake_data, populate_fake_data


assert "MONGODB_CONNECTION_STRING" in os.environ, (
    "Error. Cannot proceed when missing the value of MONGODB_CONNECTION_STRING from environment.\n"
    "This represents the connection string to be used by pymongo.\n"
    "\n"
    "It doesn't need to be the production database, but it does need to be\n"
    "some instance of mongodb."
)


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app(
        extra_config={
            "TESTING": True,
            "LOGIN_DISABLED": True,
            "MONGODB_CONNECTION_STRING": os.environ["MONGODB_CONNECTION_STRING"],
            "MONGODB_DATABASE_NAME": os.environ.get(
                "MONGODB_DATABASE_NAME", "clockwork"
            ),
        }
    )

    # We thought that the LoginManager module would check for the
    # presence of "TESTING" and we wouldn't need to also set
    # "LOGIN_DISABLED" in the config, but it turns out that we
    # need to do it.

    # create the database and load test data
    with app.app_context():
        init_db()
        db = get_db()
        cleanup_function = populate_fake_data(
            db[current_app.config["MONGODB_DATABASE_NAME"]]
        )

    yield app

    # You can close file descriptors here and do other cleanup.
    #
    cleanup_function()


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def app_with_login():
    """Create and configure a new app instance with local login enabled."""
    app = create_app(
        extra_config={
            "TESTING": True,
            "LOGIN_DISABLED": False,
            "PREFERRED_URL_SCHEME": "https",
            "MONGODB_CONNECTION_STRING": os.environ["MONGODB_CONNECTION_STRING"],
            "MONGODB_DATABASE_NAME": os.environ.get(
                "MONGODB_DATABASE_NAME", "clockwork"
            ),
        }
    )

    # create the database and load test data
    with app.app_context():
        init_db()
        db = get_db()
        cleanup_function = populate_fake_data(
            db[current_app.config["MONGODB_DATABASE_NAME"]]
        )

    yield app

    # You can close file descriptors here and do other cleanup.
    #
    cleanup_function()


@pytest.fixture
def client_with_login(app_with_login):
    """A test client for the app."""
    with app_with_login.test_client() as client:
        yield client


@pytest.fixture
def user(app):
    """
    Returns a test user that's present in the database.

    The notion of whether this user is "authenticated" with flask_login
    or not is not relevant, because when config['TESTING'] is set
    it disables everything from flask_login.
    No need to bother with LoginManager and such.
    """

    with app.app_context():
        # we need an app context because we'll be contacting the database,
        # and the database deals with "g" which is in the app context

        user_desc = {
            "id": "135798713318272451447",
            "name": "test",
            "email": "test@mila.quebec",
            "profile_pic": "",
            "clockwork_api_key": "000aaa",
        }
        user = User.get(user_desc["id"])
        # Doesn't exist? Add to database.
        if not user:
            User.add_to_database(**user_desc)
            user = User.get(user_desc["id"])

        # login_user(user)  # error : working outside of context
        return user

    # Why not something like this?
    # login_user(user)
    # yield user
    # logout_user(user)


@pytest.fixture
def valid_rest_auth_headers():
    s = f"{os.environ['clockwork_tools_test_EMAIL']}:{os.environ['clockwork_tools_test_CLOCKWORK_API_KEY']}"
    encoded_bytes = base64.b64encode(s.encode("utf-8"))
    encoded_s = str(encoded_bytes, "utf-8")
    return {"Authorization": f"Basic {encoded_s}"}


# How do we do something like that, but using Google OAuth instead?
# Maybe we don't need any of the following lines commented out.

# class AuthActions(object):
#     def __init__(self, client):
#         self._client = client

#     def login(self, username="test", password="test"):
#         return self._client.post(
#             "/auth/login", data={"username": username, "password": password}
#         )

#     def logout(self):
#         return self._client.get("/auth/logout")


# @pytest.fixture
# def auth(client):
#     return AuthActions(client)
