from flask import Blueprint, request
from flask.json import jsonify

from clockwork_web.core.hardware_helper import get_hardware_info, get_hardwares

# Prefix the endpoint
flask_api = Blueprint("rest_hardware", __name__)


@flask_api.route("/hardware/gpu/one")
def route_api_v1_hardware_gpu_one():
    """
    .. :quickref: returns the information related to one GPU (corresponding to
        the name given as argument)
    """
    # Parse the arguments
    gpu_name = request.args.get("gpu_name", None)
    if gpu_name is None:
        return jsonify("Missing argument gpu_name."), 400
    return get_hardware_info(gpu_name, "gpu")


@flask_api.route("/hardware/gpu/list")
def route_api_v1_hardware_gpu_list():
    """
    .. :quickref: lists all the GPU used
    """
    return get_hardwares("gpu")
