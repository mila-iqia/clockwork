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

# from clockwork_web.user import User
from clockwork_web.config import get_config, register_config

from test_common.fake_data import fake_data, populate_fake_data

register_config("clockwork.test.email")
register_config("clockwork.test.api_key")


@pytest.fixture(scope="module")
def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app(
        extra_config={
            "TESTING": True,
            "LOGIN_DISABLED": True,
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
        cleanup_function = populate_fake_data(db, mutate=True)

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
        }
    )

    # create the database and load test data
    with app.app_context():
        init_db()
        db = get_db()
        cleanup_function = populate_fake_data(db)

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
def valid_rest_auth_headers():
    s = f"{get_config('clockwork.test.email')}:{get_config('clockwork.test.api_key')}"
    encoded_bytes = base64.b64encode(s.encode("utf-8"))
    encoded_s = str(encoded_bytes, "utf-8")
    return {"Authorization": f"Basic {encoded_s}"}


@pytest.fixture
def known_user(app, fake_data):
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]
    known_settings = known_user["web_settings"]

    # Use the app context
    with app.app_context():
        try:
            yield known_user
        finally:
            # reset_settings
            users_collection = get_db()["users"]
            users_collection.update_one(
                {"mila_email_username": known_mila_email_username},
                {"$set": {"web_settings": known_settings}},
            )
