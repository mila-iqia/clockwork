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
# import nodes_routes
from web_server import jobs_routes


def create_app(extra_config:dict):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    for (k, v) in extra_config.items():
        app.config[k] = v

    # app.register_blueprint(nodes_routes.flask_api, url_prefix="/nodes")
    app.register_blueprint(jobs_routes.flask_api, url_prefix="/jobs")

    @app.route("/")
    def index():
        # return render_template("index.html")
        return redirect("jobs/")

    # TODO : Maybe you can add the /login stuff from Google OAuth
    #        just like a blueprint being registered?
    #        It would be the first time I did this.
    # app.register_blueprint(login_routes.login_routes, url_prefix="/login")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
