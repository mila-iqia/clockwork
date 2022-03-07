"""
Helper functions in order to handle hardware data.
"""

from flask.globals import current_app
from flask.json import jsonify

from ..db import get_db
from enum import Enum


def get_hardware_info(hardware_name):
    """
    Get information on a specific hardware defined by its name.

    Parameters:
        hardware_name   Name of the requested hardware

    Returns:
        A dictionary describing the requested hardware if it has been found.
        An empty dictionary otherwise
    """
    # Check the gpu_name type
    if isinstance(hardware_name, str) and len(hardware_name) > 0:
        db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        # Find one entry presenting the name corresponding to gpu_name
        requested_hardware = db["hardware"].find_one(
            {"name": hardware_name}, {"_id": 0}
        )
        if requested_hardware is not None:
            return requested_hardware

    return {}


def get_hardwares():
    """
    Get a list of the different known GPUs.

    Returns:
        A list of dictionaries describing the requested GPUs
    """
    db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    return {"hardware_list": list(db["hardware"].find({}, {"_id": 0}))}
    return {}


def get_all_hardwares():
    """
    Get a list of the different known GPUs.

    Returns:
        A list of dictionaries describing the different GPUs.
    """
    db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    return {"hardware_list": list(db["hardware"].find({}, {"_id": 0}))}
