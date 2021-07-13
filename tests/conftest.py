"""
This is a special file that pytest will find first.
"""

import os
import json
from flask.globals import current_app

import pytest

import web_server
from web_server.main_http_server import create_app
from web_server.db import get_db, init_db
from web_server.user import User

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
    app = create_app(extra_config={ "TESTING": True,
                                    "MONGODB_CONNECTION_STRING": os.environ["MONGODB_CONNECTION_STRING"],
                                    "MONGODB_DATABASE_NAME": os.environ.get("MONGODB_DATABASE_NAME", "clockwork")})

    # If we understand things correctly, the LoginManager module
    # will check for the presence of "TESTING", and we don't need to
    # also set "LOGIN_DISABLED" in the config.

    # create the database and load test data
    with app.app_context():
        init_db()
        db = get_db()
        populate_fake_data(db[current_app.config["MONGODB_DATABASE_NAME"]])

    yield app

    # You can close file descriptors here and do other cleanup.


@pytest.fixture
def client(app):
    """A test client for the app."""
    # The `test_client` method comes from Flask. Not us.
    # https://github.com/pallets/flask/blob/93dd1709d05a1cf0e886df6223377bdab3b077fb/src/flask/app.py#L997
    return app.test_client()


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

        user_desc = {"id": "135798713318272451447",
                    "name": "test",
                    "email": "test@example.com",
                    "profile_pic": ""}
        user = User(**user_desc)
        # Doesn't exist? Add to database
        if not User.get(user_desc["id"]):
            User.create(**user_desc)
        
        return user



def populate_fake_data(db_insertion_point, json_file=None):
    """
    This json file should contain a dict with keys "users", "jobs", "nodes".
    Not all those keys need to be present. If they are,
    then we will update the corresponding collections in the database.

    `db_insertion_point` is something like db["slurm"] or db["clockwork"],
    at the level right before which we specify the collection.
    It's hard to find the right word for this, because mongodb would
    call it a "database", but in the context of this flask app we refer
    to the database connection as the "db".
    """

    if json_file is None:
        json_file = os.path.join(   os.path.dirname(os.path.abspath(__file__)),
                                    "fake_data.json")

    assert os.path.exists(json_file), (
        f"Failed to find the fake data file to populate the database for testing: {json_file}."
    )
    with open(json_file, "r") as f:
        E = json.load(f)
    
    for k in ["users", "jobs", "nodes"]:
        if k in E:
            for e in E[k]:
                db_insertion_point[k].insert_one(e)


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