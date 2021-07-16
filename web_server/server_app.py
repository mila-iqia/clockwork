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
from flask import Flask, redirect, render_template
from flask_login import (
    current_user,
    LoginManager
)
# import nodes_routes
import jobs_routes
import login_routes
from user import User


def create_app(extra_config:dict):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    for (k, v) in extra_config.items():
        app.config[k] = v

    # app.register_blueprint(nodes_routes.flask_api, url_prefix="/nodes")
    app.register_blueprint(jobs_routes.flask_api, url_prefix="/jobs")

    # TODO : Maybe you can add the /login stuff from Google OAuth
    #        just like a blueprint being registered?
    #        It would be the first time I did this.
    app.register_blueprint(login_routes.flask_api, url_prefix="/login")

    # User session management setup
    # https://flask-login.readthedocs.io/en/latest
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return "You must be logged in to access this content.", 403

    # Flask-Login helper to retrieve a user from our db
    @login_manager.user_loader
    def load_user(user_id):
        # gyom : I don't know when this is called, though...
        user = User.get(user_id)
        # When `user` is None, we return None and that's what `load_user` wants.

        # TODO : need to login_user again or something? current_user.
        print(f"In @login_manager.user_loader def load_user(user_id), we have that user.is_authenticated is {user.is_authenticated}. Also, `user is None` is {user is None}.")
        return user


    @app.route("/")
    def index():
        if current_user.is_authenticated:
            print("in route for '/'; redirecting to jobs/")
            return redirect("jobs/")
        else:
            print("in route for '/'; render_template('index_outside.html')")
            return render_template("index_outside.html")
            # return redirect("jobs/")



    return app
