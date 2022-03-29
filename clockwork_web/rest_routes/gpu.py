"""
Define the API requests related to the GPU.
"""

from flask import Blueprint, request
from flask.json import jsonify

from clockwork_web.core.gpu_helper import get_gpu_info, get_gpu_list

# Prefix the endpoint
flask_api = Blueprint("rest_gpu", __name__)


@flask_api.route("/gpu/one")
def route_api_v1_gpu_one():
    """
    .. :quickref: return the information related to one GPU (corresponding to
        the name given as argument)
    """
    # Parse the arguments
    gpu_name = request.args.get("gpu_name", None)
    # Check if the mandatory argument 'gpu_name' has been provided, and return
    # a 'Bad Request' code if not
    if gpu_name is None:
        return jsonify("Missing argument gpu_name."), 400
    # Otherwise, retrieve and return the GPU information
    return get_gpu_info(gpu_name)


@flask_api.route("/gpu/list")
def route_api_v1_gpu_list():
    """
    .. :quickref: list all the GPUs' specifications known by Clockwork
    """
    return jsonify(get_gpu_list())
