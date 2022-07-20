#!/usr/bin/env python3

from clockwork_web.config import register_config
from clockwork_web.db import init_db, get_db
from clockwork_web.server_app import create_app
from test_common.fake_data import populate_fake_data


# Register the elements to access the database
register_config("mongo.connection_string", "")
register_config("mongo.database_name", "clockwork")

# Create a test context
app = create_app(extra_config={"TESTING": True, "LOGIN_DISABLED": True})

# Within this context of tests
with app.app_context():
    # Initialize the database
    init_db()
    db = get_db()
    # Insert fake data in it
    cf = populate_fake_data(db)
