from flask import request, make_response
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from clockwork_web.core.nodes_helper import get_nodes
from clockwork_web.core.common import get_filter_from_request_args

from flask import Blueprint

flask_api = Blueprint("rest_nodes", __name__)


@flask_api.route("/nodes/list")
def route_api_v1_nodes_list():
    """
    Take one optional args "cluster_name", as in "/nodes/list?cluster_name=beluga".

    .. :quickref: list all Slurm nodes
    """
    filter = get_filter_from_request_args(["cluster_name"])

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        resp = jsonify("Authorization error.")
        resp.status_code = 401  # unauthorized
        return resp

    resp = jsonify(get_nodes(filter))
    resp.status_code = 200
    return resp


@flask_api.route("/nodes/one")
def route_api_v1_nodes_one():
    """
    Takes one mandatory args "name", as in "/nodes/one?name=cn-a003".
    This could take a "cluster_name" args if, for some freak reason,
    we have two clusters that have clashes with their host names.

    .. :quickref: list one Slurm node
    """
    filter = get_filter_from_request_args(["cluster_name", "name"])

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        resp = jsonify("Authorization error.")
        resp.status_code = 401  # unauthorized
        return resp

    LD_nodes = get_nodes(filter)

    if len(LD_nodes) == 0:
        # Not a great when missing the value we want, but it's an acceptable answer.
        resp = jsonify({})
        resp.status_code = 200
        return resp
    if len(LD_nodes) > 1:
        # This is not a situation that should even happen, and it's a sign of data corruption.
        resp = jsonify(
            f"Found {len(LD_nodes)} nodes with filter {filter}. Not sure what to do about these cases."
        )
        resp.status_code = 500  # server error
        return resp

    D_node = LD_nodes[0]

    resp = jsonify(D_node)
    resp.status_code = 200
    return resp
