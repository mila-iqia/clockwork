from pymongo import MongoClient

from flask import current_app
from flask import g
from flask.cli import with_appcontext

from clockwork_web.config import get_config, register_config

register_config("mongo.connection_string", "")
register_config("mongo.database_name", "clockwork")


def _get_db():
    """Connect to the application's configured database.

    The connection is unique for each request and will be reused
    if this is called again in the same request context.

    Returns:
        MongoClient: a client to the mongodb server (but not a specific collection)
    """
    if "db" not in g:
        g.db = MongoClient(get_config("mongo.connection_string"))

    return g.db


def get_db():
    return _get_db()[get_config("mongo.database_name")]


def close_db(e=None):
    """If this request connected to the database, close the connection.

    Disclaimer: The `e=None` code is cargo code. Not sure why it's there.
    Not really worth investigating too deeply now, but maybe later.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


# Note that all the `init_db` and `init_app` code were
# taken from a tutorial about pytest in which they really
# want to clear the database at the beginning.
# We don't want that when using the app for real,
# so it seems like a bad idea to clear the database
# in the `init_app` function.
#
# TODO : If `init_app` is used only in testing,
#        then we can put all that clear/reset stuff
#        back in.


def init_db():
    """Clear existing data and create new tables.

    TODO : Think a bit more about the whole idea of clearing
    the database when you initialize it like that. It's fine
    in development, but it would be a bad idea if our production
    server kept wiping the database every time we restarted it.

    Some better design is needed here to have a better strategy
    that allows proper testing, development and deployment.
    """
    db = _get_db()

    # Clear out everything, in case there's stuff leftover from a previous run.
    for collection in ["jobs", "nodes", "users"]:
        db[get_config("mongo.database_name")][collection].delete_many({})

    # TODO : We may have some minor things to do here
    #        to setup some basic information in the database.

    # with current_app.open_resource("schema.sql") as f:
    #     db.executescript(f.read().decode("utf8"))


@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
