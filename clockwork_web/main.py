"""
We don't want to create the `app` in the global scope of "server_app.py"
because that would clash with our structure for testing.

We do need it to be somewhere, though, in the global scope of some file,
so that gcloud can run it with the equivalent of 
    entrypoint: gunicorn -b :$PORT main:app

That leads here, to this file, which is just a barebone launcher.
"""

from .config import get_config, register_config, boolean, string, integer, anything
from .server_app import create_app
import logging

"""
By default, we require only environment variable "MONGODB_CONNECTION_STRING"
to know how to connect to the mongodb database.

We would only disable logins manually when trying out certain
things locally, like doing development on the HTML/JS, and we
wanted to avoid authenticating with Google every time we relaunch.

We should pick some kind of convention by which, when we disable
the login, we set the user to be "mario" or something like that.
"""

register_config("flask.testing", False, validator=boolean)
register_config("flask.login_disabled", False, validator=boolean)

register_config("sentry.dns", "", validator=string)
register_config("sentry.traces_sample_rate", 1.0, validator=anything)

register_config("logging.level", 40, validator=integer)
register_config("logging.stderr", True, validator=boolean)
register_config("logging.journald", False, validator=boolean)

logger = logging.getLogger()
logger.setLevel(get_config("logging.level"))

if get_config("logging.stderr"):
    logger.addHandler(logging.StreamHandler())

if get_config("logging.journald"):
    from systemd.journal import JournalHandler

    logger.addHandler(JournalHandler())


sentry_dns = get_config("sentry.dns")
if sentry_dns:
    # Not sure about how sentry works, but it probably does
    # some behind-the-scenes things before the flask components
    # are loaded. It's not clear to me if we really need to ensure
    # that it gets loaded before we import the `create_app` method
    # (i.e. before anything pertaining to Flask gets imported).

    # We can avoid using those libraries if we don't want to use Sentry.io.
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=sentry_dns,
        integrations=[
            FlaskIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend having a lower value in production.
        traces_sample_rate=get_config("sentry.traces_sample_rate"),
    )
    logging.info("Loaded sentry logging at %s.", sentry_dns)
else:
    logging.info(
        "Not loading sentry because the sentry.dns config is empty or is missing."
    )


app = create_app(
    extra_config={
        "TESTING": get_config("flask.testing"),
        "LOGIN_DISABLED": get_config("flask.login_disabled"),
    }
)
