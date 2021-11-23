"""
This is a special file that pytest will find first.
"""

import os
import json

import pytest

# included to obtain its __file__ and not
# really to use the `extra_filters` themselves
from slurm_state import extra_filters


@pytest.fixture
def mila_related_slurm_allocations():
    """
    Creates a file called "mila_related_slurm_allocations.json"
    for `slurm_state.extra_filters`, and then we just fill it
    with the value "fake_allocation_name".
    """

    json_file = os.path.join(
        os.path.dirname(os.path.abspath(extra_filters.__file__)),
        "mila_related_slurm_allocations.json",
    )
    with open(json_file, "w") as f:
        json.dump(["fake_allocation_name"], f)

    yield app

    # You can close file descriptors here and do other cleanup.
    #
    # 2021-08-11 : Okay, so we have important decisions to make here,
    #              because it's pretty hard to test clockwork_tools without
    #              fake data in the database, but the fake_data.json lives
    #              in clockword_web_test. Maybe we can remove the cleanup step
    #              from those tests and rely on side-effects from pytest
    #              running the clockwork_web_test first.
    #              This is not nice, but on the flipside, we might need
    #              to rethink how those tests are written to begin with,
    #              and possibly add the fake data as part of the mongodb
    #              component of Docker Compose when running in test mode.
    #              Tests from clockwork_tools aren't supposed to muck with the database.
    #
    cleanup_function()


@pytest.fixture
def client(app):
    """A test client for the app."""
    # The `test_client` method comes from Flask. Not us.
    # https://github.com/pallets/flask/blob/93dd1709d05a1cf0e886df6223377bdab3b077fb/src/flask/app.py#L997
    return app.test_client()
