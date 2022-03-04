"""
This is a special file that pytest will find first.
"""

import os
import pytest

import scripts

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

    # create the database and load test data
    with app.app_context():
        init_db()
    
    yield app

    # You can close file descriptors here and do other cleanup.
    #
    #cleanup_function()


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client
