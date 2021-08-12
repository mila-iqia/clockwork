from flask import request
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from clockwork_web.core.nodes_helper import get_nodes
from clockwork_web.core.common import get_filter_from_request_args

from flask import Blueprint
flask_api = Blueprint('rest_nodes', __name__)


@flask_api.route('/nodes/list')
def route_api_v1_nodes_list():
    """
    Take one optional args "cluster_name", as in "/nodes/list?cluster_name=beluga".
    """
    filter = get_filter_from_request_args(["cluster_name"])

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized

    return jsonify(get_nodes(filter)), 200


@flask_api.route('/nodes/one')
def route_api_v1_nodes_one():
    """
    Takes one mandatory args "name", as in "/nodes/one?name=cn-a003".
    This could take a "cluster_name" args if, for some freak reason,
    we have two clusters that have clashes with their host names.
    """
    filter = get_filter_from_request_args(["cluster_name", "name"])

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized

    return jsonify(get_nodes(filter)), 200