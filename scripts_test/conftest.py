"""
This is a special file that pytest will find first.
"""

import pytest

import scripts
from scripts_test.config import register_config

register_config("mongo.connection_string", "")
register_config("mongo.database_name", "clockwork")


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app(extra_config={"TESTING": True, "LOGIN_DISABLED": True})

    # create the database and load test data
    with app.app_context():
        init_db()

    yield app

    # You can close file descriptors here and do other cleanup.
    #
    # cleanup_function()


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client
