
import os
import pytest

from pymongo import MongoClient

import mila_tools
import mila_tools.client

from clockwork_web.db import get_db, init_db
from clockwork_web_test.conftest import populate_fake_data

@pytest.fixture
def config():
    """
    Better here to fail completely if any of those values are empty.
    """
    config = {
        'host': os.environ['MILA_TOOLS_TEST_HOST'],
        'port': os.environ['MILA_TOOLS_TEST_PORT'],
        'email': os.environ['MILA_TOOLS_TEST_EMAIL'],
        'clockwork_api_key': os.environ['MILA_TOOLS_TEST_CLOCKWORK_API_KEY']}
    for (k, v) in config.items():
        assert v, (f"Missing value in environment for mila_tools configuration {k}.")
    return config

@pytest.fixture
def db_with_fake_data():
    """
    This is a bit of a weird fixture. It's just a way to make sure that
    the database has fake data from clockwork_web_test/fake_data.json in it,
    but we don't want to tests to play with the actual database.
    """

    assert 'MONGODB_CONNECTION_STRING' in os.environ
    assert 'MONGODB_DATABASE_NAME' in os.environ

    db = MongoClient(os.environ['MONGODB_CONNECTION_STRING'])
    cleanup_function = populate_fake_data(db[os.environ['MONGODB_DATABASE_NAME']])
    yield db  # This would be `yield None` instead to make our intentions more explicit.
    cleanup_function()

@pytest.fixture
def mtclient(config, db_with_fake_data):
    return mila_tools.client.MilaTools(config)