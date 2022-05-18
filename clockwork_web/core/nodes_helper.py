"""
Functions in this file are things that are called after the authentication step.
They don't do any authentication themselves, but are serving the browser_routes
and rest_routes, which are just fronts for these functions here.
"""

from flask.globals import current_app
from clockwork_web.db import get_db


def get_filter_node_name(node_name):
    """
    Looks rather useless right now, but this implements the
    little translation needed between the "node_name" that we
    refer to in Clockwork and the actual "name" field in the
    Slurm entries. We use "node_name" in Clockwork to make it
    more explicit, but we don't want to disturb the fields
    returned from Slurm.
    """
    if node_name is None:
        return {}
    else:
        return {"slurm.name": node_name}


def get_nodes(mongodb_filter: dict = {}) -> list:
    """
    Talk to the database and get the information.

    Returns a list of dict with the properties of nodes.
    """
    # Connect to the database
    mc = get_db()

    # Retrieve the list of nodes corresponding to the criteria
    # - The "mongodb_filter" is used to select the nodes we are looking for
    # - The second parameter ({"_id": 0}) is used to delete the "_id" element
    #   of each returned node
    LD_nodes = list(mc["nodes"].find(mongodb_filter, {"_id": 0}))
    return LD_nodes
