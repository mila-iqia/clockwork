"""
Define the API requests related to the nodes.
"""

from flask import request, make_response
from flask.json import jsonify
from .authentication import authentication_required

from clockwork_web.core.nodes_helper import get_nodes, get_filter_name
from clockwork_web.core.jobs_helper import (
    combine_all_mongodb_filters,
    get_filter_cluster_name,
)
from clockwork_web.core.gpu_helper import get_gpu_info

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
    Take one mandatory args "name", as in "/nodes/one?name=cn-a003".
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


@flask_api.route("/nodes/one/gpu")
@authentication_required
def route_api_v1_nodes_one_gpu():
    """
    Describe the GPU of a node.

    Take one mandatory "node_name", as in "/nodes/one/gpu?node_name=cn-a003".
    This could also take a "cluster_name" argument if we have two clusters that
    have clashes with their host names.

    Return the specifications of a node's GPU. The returned dictionary presents
    the following format:
    {
        "name": <gpu_name>,
        "vendor": <gpu_vendor>,
        "ram": <ram_in_gb>,
        "cuda_cores": <cuda_cores>,
        "tensor_cores": <tensor_cores>,
        "tflops_fp32": <tflops_fp32>
    }
    with:
        - <gpu_name> a string presenting the GPU name as described in the Slurm report
        - <gpu_vendor> a string containing the name of the GPU's vendor
        - <ram_in_gb> an integer which is the number of GB of the GPU's RAM
        - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
        - <tensor_cores> an integer presenting the number of tensor cores of the GPU
        - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
          (theoretical computing power with single-precision)

    .. :quickref: describe the GPU of a node
    """
    # Parse the arguments
    node_name = request.args.get("node_name", None)
    cluster_name = request.args.get("cluster_name", None)

    # Check if the mandatory argument 'node_name' has been provided, and return
    # a 'Bad Request' code if not
    if node_name is None:
        return jsonify("Missing argument node_name."), 400

    # Retrieve the node's information given by the user
    node_filter = get_filter_name(node_name)
    cluster_filter = get_filter_cluster_name(cluster_name)

    # Combine the filters on the node name and the cluster name in order to
    # search in the database
    filter = combine_all_mongodb_filters(node_filter, cluster_filter)

    # Retrieve the corresponding node, according to the filters
    node_information = get_nodes(filter)

    # Check if the node has been correctly retrieved
    if len(node_information) == 1:
        # Get the GPU name
        try:
            gpu_name = node_information[0]["cw"]["gpu"]["gpu_name"]
        except:
            return {}
        # Retrieve the GPU information
        return get_gpu_info(gpu_name)

    # Otherwise, return an empty dictionary
    return {}
