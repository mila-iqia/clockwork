"""

export FLASK_RUN_PORT=5555
export FLASK_DEBUG=1
export FLASK_APP=main_http_server.py

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
# import nodes_routes
import jobs_routes
import settings_routes
import login_routes
from user import User


def create_app(extra_config:dict):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    for (k, v) in extra_config.items():
        app.config[k] = v

    # app.register_blueprint(nodes_routes.flask_api, url_prefix="/nodes")
    app.register_blueprint(jobs_routes.flask_api, url_prefix="/jobs")
    app.register_blueprint(settings_routes.flask_api, url_prefix="/settings")

    # TODO : Maybe you can add the /login stuff from Google OAuth
    #        just like a blueprint being registered?
    #        It would be the first time I did this.
    app.register_blueprint(login_routes.flask_api, url_prefix="/login")

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
