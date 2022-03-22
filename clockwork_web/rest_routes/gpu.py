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
    Return the information related to one GPU.

    Take one mandatory "gpu_name", as in "/gpu/one?gpu_name=rtx8000".
    The name is used to identify the GPU in the Clockwork database. Thus, it is
    based on the "cw_name" of the GPU, and not its "name" argument.

    Return the specifications of the requested GPU. The returned dictionary
    presents the following format:
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
        - <ram_in_gb> a float which is the number of GB of the GPU's RAM
        - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
        - <tensor_cores> an integer presenting the number of tensor cores of the GPU
        - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
          (theoretical computing power with single-precision)

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
    List the GPU specifications stored in the database.

    Return a list of the specifications stored in the database. This is a list
    of dictionaries describing each one a GPU. Such a dictionary presents the
    following format:
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
        - <ram_in_gb> a float which is the number of GB of the GPU's RAM
        - <cuda_cores> an integer presenting the number of CUDA cores of the GPU
        - <tensor_cores> an integer presenting the number of tensor cores of the GPU
        - <tflops_fp32> a float presenting the number of TFLOPS for a FP32 performance
          (theoretical computing power with single-precision)

    .. :quickref: list all the GPUs used
    """
    return get_gpu_list()
