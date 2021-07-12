from pymongo import MongoClient

from flask import current_app
from flask import g
from flask.cli import with_appcontext


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = MongoClient(current_app.config["CLOCKWORK_MONGODB_DATABASE"])

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
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
    """Clear existing data and create new tables."""
    db = get_db()

    # TODO : We probably have some minor things to do here
    #        to setup some basic information in the database.

    # with current_app.open_resource("schema.sql") as f:
    #     db.executescript(f.read().decode("utf8"))


#@with_appcontext
#def init_db_command():
#    """Clear existing data and create new tables."""
#    init_db()


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    # app.cli.add_command(init_db_command)