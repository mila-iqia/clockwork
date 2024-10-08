"""
We don't want to create the `app` in the global scope of "server_app.py"
because that would clash with our structure for testing.

We do need it to be somewhere, though, in the global scope of some file,
so that gcloud can run it with the equivalent of 
    entrypoint: gunicorn -b :$PORT main:app

That leads here, to this file, which is just a barebone launcher.
"""

from .config import (
    get_config,
    register_config,
    boolean,
    string,
    integer,
    anything,
    string_choices,
)
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

register_config("sentry.dsn", "", validator=string)
register_config("sentry.dns", "", validator=string)  # deprecated because typo
register_config("sentry.traces_sample_rate", 1.0, validator=anything)

LOGGING_LEVEL_MAPPING = dict(
    everything=logging.NOTSET,
    debug=logging.DEBUG,
    info=logging.INFO,
    warning=logging.WARNING,
    error=logging.ERROR,
    critical=logging.CRITICAL,
)
register_config(
    "logging.level", "error", validator=string_choices(*LOGGING_LEVEL_MAPPING.keys())
)

register_config("logging.stderr", False, validator=boolean)
register_config(
    "logging.level_stderr",
    "info",
    validator=string_choices(*LOGGING_LEVEL_MAPPING.keys()),
)
register_config(
    "logging.level_werkzeug",
    "info",
    validator=string_choices(*LOGGING_LEVEL_MAPPING.keys()),
)

register_config("logging.journald", False, validator=boolean)
register_config("logging.otel", "", validator=string)

logger = logging.getLogger()

logger.setLevel(LOGGING_LEVEL_MAPPING[get_config("logging.level")])

if get_config("logging.stderr"):

    class ConsoleFormatter(logging.Formatter):
        def __init__(self, fstring=None, formats=None):
            """
            A fancier formatter for stderr, with different color depending on the message level.
            """
            self.formats = formats
            if formats is None:
                self.formats = {
                    logging.DEBUG: "\x1b[32;2m",
                    logging.INFO: "\x1b[30m",
                    logging.WARNING: "\x1b[34;1m",
                    logging.ERROR: "\x1b[31;1m",
                    logging.CRITICAL: "\x1b[35;1m",
                }
            self._clean = "\x1b[0m"

            self.formatstr = fstring
            if fstring is None:
                self.formatstr = "{levelname}:{name}:{message}"

        def format(self, record):
            return "".join(
                [
                    self.formats[record.levelno],
                    self.formatstr.format(
                        message=record.getMessage(), **(record.__dict__)
                    ),
                    self._clean,
                ]
            )

    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(stderr_handler)
    logger.setLevel(LOGGING_LEVEL_MAPPING[get_config("logging.level_stderr")])
    logging.info("Logging to stderr")
    # logging.debug ("test level DEBUG")
    # logging.info ("test level INFO")
    # logging.warning ("test level WARNING")
    # logging.error ("test level ERROR")
    # logging.critical ("test level CRITICAL")

werkzeug_logger = logging.getLogger("werkzeug")
if werkzeug_logger != None:
    werkzeug_logger.setLevel(
        LOGGING_LEVEL_MAPPING[get_config("logging.level_werkzeug")]
    )

if get_config("logging.journald"):
    from systemd.journal import JournalHandler

    logger.addHandler(JournalHandler())
    logging.info("Logging to journald")


if get_config("logging.otel") != "":
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    logger_provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": "clockwork",
                "service.instance.id": os.uname().nodename,
            }
        ),
    )
    set_logger_provider(logger_provider)

    otlp_exporter = OTLPLogExporter(endpoint=get_config("logging.otel"))
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)

sentry_dsn = get_config("sentry.dsn")
if not sentry_dsn:
    sentry_dsn = get_config("sentry.dns")  # Old typo
if sentry_dsn:
    # Not sure about how sentry works, but it probably does
    # some behind-the-scenes things before the flask components
    # are loaded. It's not clear to me if we really need to ensure
    # that it gets loaded before we import the `create_app` method
    # (i.e. before anything pertaining to Flask gets imported).

    # We can avoid using those libraries if we don't want to use Sentry.io.
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend having a lower value in production.
        traces_sample_rate=get_config("sentry.traces_sample_rate"),
    )
    logging.info("Loaded sentry logging at %s.", sentry_dsn)
else:
    logging.info(
        "Not loading sentry because the sentry.dsn config is empty or is missing."
    )


app = create_app(
    extra_config={
        "TESTING": get_config("flask.testing"),
        "LOGIN_DISABLED": get_config("flask.login_disabled"),
    }
)
