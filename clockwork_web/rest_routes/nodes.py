from flask import request
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from clockwork_web.core.nodes_helper import get_nodes

from flask import Blueprint
flask_api = Blueprint('rest_nodes', __name__)

@flask_api.route('/nodes/list')
def route_api_v1_nodes_list():

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized

    return jsonify(get_nodes()), 200