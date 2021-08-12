"""

export FLASK_RUN_PORT=5555
export FLASK_DEBUG=1
export FLASK_APP=main.py

# if I didn't use `python3` directly, flask would use the wrong python interpreter

# local connections only
python3 -m flask run  
# outside
python3 -m flask run --host=0.0.0.0

"""

import os
from flask import Flask, redirect, render_template, url_for
from flask_login import (
    current_user,
    LoginManager
)
from .browser_routes.nodes import flask_api as nodes_routes_flask_api
from .browser_routes.jobs import flask_api as jobs_routes_flask_api
# from .jobs_routes import flask_api as jobs_routes_flask_api  # TODO: this will be updated as well with new pattern
from .settings_routes import flask_api as settings_routes_flask_api
from .login_routes import flask_api as login_routes_flask_api
from .user import User
from .rest_routes.jobs import flask_api as rest_jobs_flask_api
from .rest_routes.nodes import flask_api as rest_nodes_flask_api

def create_app(extra_config:dict):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    for (k, v) in extra_config.items():
        app.config[k] = v

    app.register_blueprint(nodes_routes_flask_api, url_prefix="/nodes")
    app.register_blueprint(jobs_routes_flask_api, url_prefix="/jobs")
    app.register_blueprint(settings_routes_flask_api, url_prefix="/settings")

    # TODO : Maybe you can add the /login stuff from Google OAuth
    #        just like a blueprint being registered?
    #        It would be the first time I did this.
    app.register_blueprint(login_routes_flask_api, url_prefix="/login")

    # TODO : See if you should include the "/jobs" part here or have it in the rest_routes/jobs.py file.
    app.register_blueprint(rest_jobs_flask_api, url_prefix="/api/v1/clusters")
    app.register_blueprint(rest_nodes_flask_api, url_prefix="/api/v1/clusters")
    


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
        # When `user` is None, we return None and that's what `load_user` wants.
        print(f"In @login_manager.user_loader def load_user(user_id), we have that user.is_authenticated is {user.is_authenticated}. Also, `user is None` is {user is None}.")
        return user


    @app.route("/")
    def index():
        """
        This route is not protected by @login_required, because it's the lobby
        where people can click on the "login" button on the web interface.
        """

        if current_user.is_authenticated:
            print("in route for '/'; redirecting to jobs/")
            # This works.
            return redirect("jobs/")
            # This fails. Not sure why. Not worth spending too much time on organizing this thing.
            # return redirect(redirect(url_for('jobs.route_index')))
        else:
            print("in route for '/'; render_template('index_outside.html')")
            return render_template("index_outside.html")


    return app
