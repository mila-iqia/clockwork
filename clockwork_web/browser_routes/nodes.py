from pprint import pprint
import re
import os
import json
import requests
import time
from collections import defaultdict


# Use of "Markup" described there to avoid Flask escaping it when passing to a template.
# https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2

from flask import Flask, Response, url_for, request, redirect, make_response, Markup
from flask import render_template, request, send_file
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper

# https://flask.palletsprojects.com/en/1.1.x/appcontext/
from flask import g

from flask_login import (
    current_user,
    login_required,
)

# As described on
#   https://stackoverflow.com/questions/15231359/split-python-flask-app-into-multiple-files
# this is what allows the factorization into many files.
from flask import Blueprint

flask_api = Blueprint("nodes", __name__)

from clockwork_web.core.nodes_helper import get_nodes
from clockwork_web.core.common import (
    get_mila_email_username,
)
from clockwork_web.core.jobs_helper import (
    get_filter_cluster_name,
    combine_all_mongodb_filters,
)
from clockwork_web.core.nodes_helper import (
    get_filter_name,
    strip_artificial_fields_from_node,
)

# Note that flask_api.route('/') will lead to a redirection with "/nodes", and pytest might not like that.


@flask_api.route("/list")
@login_required
def route_list():
    """
    Can take optional args "cluster_name" and "name",
    where "name" refers to the host name.

    .. :quickref: list all Slurm nodes as formatted html
    """
    f0 = get_filter_name(request.args.get("name", None))
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)
    LD_nodes = get_nodes(filter)

    LD_nodes = [strip_artificial_fields_from_node(D_node) for D_node in LD_nodes]

    # sanity check
    for D_node in LD_nodes:
        if D_node is None:
            return (
                render_template(
                    "error.html",
                    error_msg=f"nodes/list returned values from the data that include one empty dict.",
                ),
                400,
            )  # bad request

    return render_template(
        "nodes.html", LD_nodes=LD_nodes, mila_email_username=get_mila_email_username()
    )


@flask_api.route("/one")
@login_required
def route_one():
    """
    Same as /list but we expect to have only a single value,
    and we render the template "single_node.html" instead of "nodes.html".

    .. :quickref: list one Slurm node as formatted html
    """

    f0 = get_filter_name(request.args.get("name", None))
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)
    LD_nodes = get_nodes(filter)

    if len(LD_nodes) == 0:
        return (
            render_template(
                "error.html",
                error_msg=f"Failed to find that node in the database with name {filter['name']} and cluster_name {filter['cluster_name']}.",
            ),
            400,
        )  # bad request
    elif len(LD_nodes) > 1:
        return (
            render_template(
                "error.html",
                error_msg=f"Found more than one entry for that node in the database with name {filter['name']} and cluster_name {filter['cluster_name']}.",
            ),
            400,
        )  # bad request

    LD_nodes = [strip_artificial_fields_from_node(D_node) for D_node in LD_nodes]

    # sanity check
    for D_node in LD_nodes:
        if D_node is None:
            return (
                render_template(
                    "error.html",
                    error_msg=f"nodes/one returned values from the data that include one empty dict.",
                ),
                400,
            )  # bad request

    D_node = LD_nodes[0]  # the one and only
    # need to format it as list of tuples for the template (unless I'm mistaken)
    LP_single_node = list(sorted(D_node.items(), key=lambda e: e[0]))
    return render_template(
        "single_nodes.html",
        LP_single_node=LP_single_node,
        mila_email_username=get_mila_email_username(),
    )
