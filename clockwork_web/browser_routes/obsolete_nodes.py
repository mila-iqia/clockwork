# TODO : This file has been abandoned for a while. Don't expect this to make sense.

import re
import os
import json
import requests
import time
from collections import defaultdict

from .nodes_routes_helper import get_nodes, strip_artificial_fields_from_node
from .jobs_routes_helper import get_jobs

# Use of "Markup" described there to avoid Flask escaping it when passing to a template.
# https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
from flask import render_template, request, send_file
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper

# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g


# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

flask_api = Blueprint("nodes_flask_api", __name__)


@flask_api.route("/")
def route_index():
    return redirect("list/")


@flask_api.route("/list/", defaults={"cluster_name": None, "reservation": None})
@flask_api.route("/list/<cluster_name>/", defaults={"reservation": None})
@flask_api.route("/list/<cluster_name>/<reservation>")
def route_list(cluster_name: str, reservation: str):

    # Note that reservation="None" is a value that we assign in sinfo.py
    # to nodes without a reservation. This is not the same as `None`
    # when there is no path passed to this method.

    filter_find = {}
    if cluster_name is not None:
        if not re.match(r"^[a-zA-Z]+$", cluster_name):
            return render_template(
                "error.html",
                error_msg="cluster_name specific contains invalid characters",
            )
        filter_find["cluster_name"] = cluster_name
    if reservation is not None:
        # `reservation` is often "None" here. The string. Not `None`.
        if not re.match(r"^[a-zA-Z\.\d\-]+$", reservation):
            return render_template(
                "error.html",
                error_msg="reservation specific contains invalid characters",
            )
        filter_find["reservation"] = reservation

    LD_nodes = get_nodes(filter_find)

    return render_template("nodes/nodes.html", LD_nodes=LD_nodes)


@flask_api.route("/single_node/<node_name>")
def route_single_node(node_name: str):

    if not re.match(r"^[a-zA-Z\d\-]+$", node_name):
        return render_template(
            "error.html", error_msg="node_name specific contains invalid characters"
        )

    LD_nodes = get_nodes({"name": node_name})
    if len(LD_nodes) == 0:
        return render_template(
            "error.html", error_msg=f"Failed to find a node with name {node_name}."
        )
    elif len(LD_nodes) > 1:
        return render_template(
            "error.html",
            error_msg=f"This is weird. We seem to have more than one node with name {node_name}.",
        )
    D_node = strip_artificial_fields_from_node(LD_nodes[0])
    # let's sort alphabetically by keys
    LP_node = list(sorted(D_node.items(), key=lambda e: e[0]))

    LD_jobs = get_jobs({"batch_host": node_name, "job_state": "RUNNING"})

    return render_template(
        "nodes/single_node.html",
        node_name=node_name,
        D_node=D_node,
        LP_node=LP_node,
        LD_jobs=LD_jobs,
    )
