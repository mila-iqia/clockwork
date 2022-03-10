"""
Helper functions in order to handle GPU information.
"""

from flask.globals import current_app
from flask.json import jsonify

from clockwork_web.db import get_db


def get_gpu_info(gpu_name):
    """
    Get information on a specific gpu defined by its name.

    Parameters:
        gpu_name   Name of the requested gpu

    Returns:
        A dictionary describing the requested gpu if it has been found.
        An empty dictionary otherwise
    """
    # Check the gpu_name type
    if isinstance(gpu_name, str) and len(gpu_name) > 0:
        db = get_db()
        # Find one entry presenting the name corresponding to gpu_name
        requested_gpu = db["gpu"].find_one({"name": gpu_name}, {"_id": 0})
        if requested_gpu is not None:
            return requested_gpu

    return {}


def get_gpu():
    """
    Get a list of the different known GPUs.

    Returns:
        A list of dictionaries describing the requested GPUs
    """
    db = get_db()
    return {"gpu_list": list(db["gpu"].find({}, {"_id": 0}))}
    return {}


def get_gpu_list():
    """
    Get a list of the different known GPUs.

    Returns:
        A list of dictionaries describing the different GPUs.
    """
    db = get_db()
    return {"gpu_list": list(db["gpu"].find({}, {"_id": 0}))}
