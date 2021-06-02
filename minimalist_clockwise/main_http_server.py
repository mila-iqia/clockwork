"""

export FLASK_RUN_PORT=5555
export FLASK_DEBUG=1
export FLASK_APP=main_http_server.py

# if I didn't use `python3` directly, flask would use the wrong python interpreter

# local connections only
python3 -m flask run  
# local connections only
python3 -m flask run --host=0.0.0.0

"""

from flask import Flask, redirect, render_template
import nodes_routes
import jobs_routes


app = Flask(__name__)

app.register_blueprint(nodes_routes.flask_api, url_prefix="/nodes")
app.register_blueprint(jobs_routes.flask_api, url_prefix="/jobs")

@app.route("/")
def hello():
    # return render_template("index.html")
    return redirect("jobs/")
    # return "Hello World!"

if __name__ == "__main__":
    app.run()
