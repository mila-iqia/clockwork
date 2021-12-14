from flask import request, make_response
from flask.json import jsonify
from .authentication import authentication_required

from clockwork_web.core.nodes_helper import get_nodes, get_filter_name
from clockwork_web.core.jobs_helper import (
    combine_all_mongodb_filters,
    get_filter_cluster_name,
)

from flask import Blueprint

flask_api = Blueprint("rest_nodes", __name__)


@flask_api.route("/nodes/list")
@authentication_required
def route_api_v1_nodes_list():
    """
    Take one optional args "cluster_name", as in "/nodes/list?cluster_name=beluga".

    .. :quickref: list all Slurm nodes
    """
    filter = get_filter_cluster_name(request.args.get("cluster_name", None))
    return jsonify(get_nodes(filter))


@flask_api.route("/nodes/one")
@authentication_required
def route_api_v1_nodes_one():
    """
    Takes one mandatory args "name", as in "/nodes/one?name=cn-a003".
    This could take a "cluster_name" args if, for some freak reason,
    we have two clusters that have clashes with their host names.

    .. :quickref: list one Slurm node
    """
    f0 = get_filter_name(request.args.get("name", None))
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)

    LD_nodes = get_nodes(filter)

    if len(LD_nodes) == 0:
        # Not a great when missing the value we want, but it's an acceptable answer.
        return jsonify({})
    if len(LD_nodes) > 1:
        # This is not a situation that should even happen, and it's a sign of data corruption.
        return (
            jsonify(
                f"Found {len(LD_nodes)} nodes with filter {filter}. Not sure what to do about these cases."
            ),
            500,
        )

    D_node = LD_nodes[0]

    return jsonify(D_node)
