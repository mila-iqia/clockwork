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
from flask import Flask, redirect, render_template, url_for
from flask_login import current_user, LoginManager
from .browser_routes.nodes import flask_api as nodes_routes_flask_api
from .browser_routes.jobs import flask_api as jobs_routes_flask_api

# from .jobs_routes import flask_api as jobs_routes_flask_api  # TODO: this will be updated as well with new pattern
from .browser_routes.settings import flask_api as settings_routes_flask_api
from .login_routes import flask_api as login_routes_flask_api
from .user import User, AnonUser
from .rest_routes.jobs import flask_api as rest_jobs_flask_api
from .rest_routes.nodes import flask_api as rest_nodes_flask_api
from .rest_routes.gpu import flask_api as rest_gpu_flask_api

from .config import register_config, get_config, string

register_config("flask.secret_key", validator=string)


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

    @app.route("/")
    def index():
        """
        This route is not protected by @login_required, because it's the lobby
        where people can click on the "login" button on the web interface.
        """

        if current_user.is_authenticated:
            print("in route for '/'; redirecting to jobs/")
            return redirect("jobs/")
        else:
            print("in route for '/'; render_template('index_outside.html')")
            return render_template("index_outside.html")

    return app
