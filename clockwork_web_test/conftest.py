"""
This is a special file that pytest will find first.
"""

import os
import json
from flask.globals import current_app

from flask_login import (
    login_user,
    logout_user
)

import pytest

import clockwork_web
from clockwork_web.server_app import create_app
from clockwork_web.db import get_db, init_db
from clockwork_web.user import User

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
                                    "LOGIN_DISABLED": True,
                                    "MONGODB_CONNECTION_STRING": os.environ["MONGODB_CONNECTION_STRING"],
                                    "MONGODB_DATABASE_NAME": os.environ.get("MONGODB_DATABASE_NAME", "clockwork")})

    # We thought that the LoginManager module would check for the
    # presence of "TESTING" and we wouldn't need to also set
    # "LOGIN_DISABLED" in the config, but it turns out that we
    # need to do it.

    # create the database and load test data
    with app.app_context():
        init_db()
        db = get_db()
        cleanup_function = populate_fake_data(db[current_app.config["MONGODB_DATABASE_NAME"]])

    yield app

    # You can close file descriptors here and do other cleanup.
    # 
    # 2021-08-11 : Okay, so we have important decisions to make here,
    #              because it's pretty hard to test mila_tools without
    #              fake data in the database, but the fake_data.json lives
    #              in clockword_web_test. Maybe we can remove the cleanup step
    #              from those tests and rely on side-effects from pytest
    #              running the clockwork_web_test first.
    #              This is not nice, but on the flipside, we might need
    #              to rethink how those tests are written to begin with,
    #              and possibly add the fake data as part of the mongodb
    #              component of Docker Compose when running in test mode.
    #              Tests from mila_tools aren't supposed to muck with the database.
    #
    cleanup_function()


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
                    "email": "test@mila.quebec",
                    "profile_pic": "",
                    "clockwork_api_key": "000aaa"}
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

    This function returns its own cleanup function that will remove
    all the entries that it has inserted. You can call it to undo
    the side-effects, and hopefully there won't be any conflict with
    real values of job_id and those fake ones.
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

    def cleanup_function():
        """
        Each of those kinds of data is identified in a unique way,
        and we can use that identifier to clean up.

        For example, when clearing out jobs, we can look at the "job_id"
        of the entries that we inserted.

        The point is that we can run a test against the production mongodb on Atlas
        and not affect the real data. If we cleared the tables completely,
        then we'd be affecting the real data in a bad way.
        """
        for (k, id_field) in [("users", "id"), ("jobs", "job_id"), ("nodes", "name")]:
            if k in E:
                for e in E[k]:
                    db_insertion_point[k].delete_many({id_field: e[id_field]})

    return cleanup_function



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