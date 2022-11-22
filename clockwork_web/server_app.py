"""
Instantiates the Flask app an wires up all the routes
in the right place.
"""


# export FLASK_RUN_PORT=5555
# export FLASK_DEBUG=1
# export FLASK_APP=main.py
#
### local connections only
# python3 -m flask run
### outside
# python3 -m flask run --host=0.0.0.0

import os
import datetime
from flask import Flask, redirect, url_for, session, request
from flask_login import current_user, LoginManager
from flask_babel import Babel
from .browser_routes.nodes import flask_api as nodes_routes_flask_api
from .browser_routes.jobs import flask_api as jobs_routes_flask_api
from .browser_routes.gpu import flask_api as gpu_routes_flask_api
from .browser_routes.users import flask_api as users_routes_flask_api
from .browser_routes.clusters import flask_api as clusters_routes_flask_api
from .browser_routes.settings import flask_api as settings_routes_flask_api

# from .jobs_routes import flask_api as jobs_routes_flask_api  # TODO: this will be updated as well with new pattern
from .login_routes import flask_api as login_routes_flask_api
from .user import User, AnonUser
from .rest_routes.jobs import flask_api as rest_jobs_flask_api
from .rest_routes.nodes import flask_api as rest_nodes_flask_api
from .rest_routes.gpu import flask_api as rest_gpu_flask_api

from .config import register_config, get_config, string, string_list, timezone

from .core.users_helper import render_template_with_user_settings


from werkzeug.urls import url_encode

register_config("flask.secret_key", validator=string)
register_config("translation.translations_folder", default="", validator=string)
register_config("translation.available_languages", default=[], validator=string_list)


def create_app(extra_config: dict):
    """Creates the Flask app with everything wired up.

    For a proper project with testing, there is a need
    to be able to instantiate our app many times instead of
    having it instantiated automatically when a certain .py
    source is parsed. Hence this function.

    Returns:
        A Flask app ready to be used.
    """
    app = Flask(__name__)
    app.secret_key = get_config("flask.secret_key")

    for (k, v) in extra_config.items():
        app.config[k] = v

    app.register_blueprint(nodes_routes_flask_api, url_prefix="/nodes")
    app.register_blueprint(jobs_routes_flask_api, url_prefix="/jobs")
    app.register_blueprint(users_routes_flask_api, url_prefix="/users")
    app.register_blueprint(gpu_routes_flask_api, url_prefix="/gpu")
    app.register_blueprint(clusters_routes_flask_api, url_prefix="/clusters")
    app.register_blueprint(settings_routes_flask_api, url_prefix="/settings")
    app.register_blueprint(login_routes_flask_api, url_prefix="/login")

    # TODO : See if you should include the "/jobs" part here or have it in the rest_routes/jobs.py file.
    app.register_blueprint(rest_jobs_flask_api, url_prefix="/api/v1/clusters")
    app.register_blueprint(rest_nodes_flask_api, url_prefix="/api/v1/clusters")
    app.register_blueprint(rest_gpu_flask_api, url_prefix="/api/v1/clusters")

    # User session management setup
    # https://flask-login.readthedocs.io/en/latest
    login_manager = LoginManager()
    login_manager.init_app(app)

    # This prevents non-fresh sessions from being carried
    # to a different IP and device. It ends up asking for login
    # more often when changing device.
    # We don't know, however, if it's going to cause issues
    # if people are logged in from two different devices
    # at the same time (e.g. desktop and laptop). Try it out.
    login_manager.session_protection = "strong"

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect("/")
        # return "You must be logged in to access this content.", 403

    # Flask-Login helper to retrieve a user from our db
    @login_manager.user_loader
    def load_user(user_id):
        user = User.get(user_id)
        # When `user` is None, we return None and that's what `load_user` wants
        return user

    login_manager.anonymous_user = AnonUser

    # Internationalization
    # https://python-babel.github.io/flask-babel/

    # Set the translations directory path
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = get_config(
        "translation.translations_folder"
    )

    # Adding a function to help with updating url params from the template
    @app.template_global()
    def modify_query(**new_values):
        args = request.args.copy()

        for key, value in new_values.items():
            args[key] = value

        return "{}?{}".format(request.path, url_encode(args))

    # Initialize Babel
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        # If the user is authenticated
        if current_user.is_authenticated:
            return current_user.get_language()

        # If the user is not authenticated
        else:
            # If no language has been previously determined, use the browser's
            # preferred language and store it to the session
            if "language" not in session:
                browser_language = request.accept_languages.best_match(
                    get_config("translation.available_languages")
                )
                session["language"] = browser_language

            return session["language"]

    # Initialize templates filters
    @app.template_filter()
    def format_date(float_timestamp):
        montreal_timezone = (
            "America/Montreal"  # For now, we display the hour in the Montreal timezone
        )
        if float_timestamp is not None:
            datetime_timestamp = datetime.datetime.fromtimestamp(float_timestamp)
            return datetime_timestamp.astimezone(timezone(montreal_timezone)).strftime(
                "%Y-%m-%d %H:%M"
            )
        else:
            return ""

    @app.template_filter()
    def check_web_settings_column_display(web_settings, page_name, column_name):
        """
        Check whether or not the web setting associated to the display of a job property
        as column on an array on the page "dashboard" or "jobs_list" is set. If it is set,
        check its boolean value.

        Such a web setting, if set, is accessible by calling web_settings[page_name][column_name].
        The different columns (ie jobs properties) for each page are now the following:
        - "dashboard" contains the properties ["clusters", "job_id", "job_name", "job_state", "start_time", "submit_time", "end_time", "links", "actions"]
        - "jobs_list" contains the properties ["clusters", "users", "job_id", "job_name", "job_state", "start_time", "submit_time", "end_time", "links", "actions"]

        Parameters:
            web_settings    A dictionary containing the preferences of the user regarding
                            the web interface display.
            page_name       The name of the page on which we should display or not the
                            job properties requested by the user in its preferences. For now,
                            the values "dashboard" or "jobs_list" are expected
            column_name     The column showing a specific job property, to display or not regarding
                            the preferences of the user.

        Returns:
            True if the web_setting is set and True, False otherwise.
        """
        return ("column_display" in web_settings) and (page_name in web_settings["column_display"]) and (column_name in web_settings["column_display"][page_name]) and web_settings["column_display"][page_name][column_name]

    @app.route("/")
    def index():
        """
        This route is not protected by @login_required, because it's the lobby
        where people can click on the "login" button on the web interface.
        """

        if current_user.is_authenticated:
            app.logger.debug("in route for '/'; redirecting to jobs/")
            return redirect("jobs/")
        else:
            app.logger.debug(
                "in route for '/'; render_template_with_user_settings('index_outside.html')"
            )
            return render_template_with_user_settings("index_outside.html")

    return app
