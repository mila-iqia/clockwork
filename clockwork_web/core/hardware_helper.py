"""
Helper functions in order to handle hardware data.
"""

from flask.globals import current_app
from flask.json import jsonify

from ..db import get_db
from enum import Enum


def get_hardware_types():
    """
    Lists all the types of hardware the database can contain.

    Returns:
        A list of strings
    """
    hardware_types = ["gpu"]
    return hardware_types


def get_hardware_info(hardware_name, hardware_type):
    """
    Get information on a specific hardware defined by its name and type.

    Parameters:
        hardware_name   Name of the requested hardware
        hardware_type   Type of the requested hardware. A list of the different
            types can be got through the function get_hardware_types

    Returns:
        A dictionary describing the requested hardware if it has been found.
        An empty dictionary otherwise
    """
    if hardware_type in get_hardware_types():
        # Check the gpu_name type
        if isinstance(hardware_name, str) and len(hardware_name) > 0:
            db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
            # Find one entry presenting the name corresponding to gpu_name
            # and the type "gpu"
            requested_hardware = db["hardware"].find_one(
                {"name": hardware_name, "type": hardware_type}, {"_id": 0}
            )
            if requested_hardware is not None:
                return requested_hardware

    return {}


def get_hardwares(hardware_type):
    """
    Get a list of the different known hardwares presenting a certain type.

    Parameters:
        hardware_type   Type of the requested hardware. A list of the different
            types can be got through the function get_hardware_types

    Returns:
        A list of dictionaries describing the requested hardwares
    """
    if hardware_type in get_hardware_types():
        db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        return {
            "hardware_list": list(
                db["hardware"].find({"type": hardware_type}, {"_id": 0})
            )
        }
    return {}


def get_all_hardwares():
    """
    Get a list of the different known hardwares.

    Returns:
        A list of dictionaries describing the different hardwares.
    """
    if hardware_type in get_hardware_types():
        db = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        return {"hardware_list": list(db["hardware"].find({}, {"_id": 0}))}
    return {}
