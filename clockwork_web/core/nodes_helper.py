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


def get_nodes(mongodb_filter: dict = {}, pagination: tuple = None) -> list:
    """
    Talk to the database and get the information.

    Parameters:
        mongodb_filter  A concatenation of the filters to apply in order to select
                        the nodes we want to retrieve from the MongoDB database
        pagination      A tuple presenting the number of elements to skip while
                        listing the nodes as first element, and, as second element,
                        the number of nodes to display from it

    Returns:
        Returns a list of dict with the properties of nodes.
    """
    # Assert that pagination is a tuple of two elements
    if not (type(pagination) == tuple and len(pagination) == 2):
        pagination = None

    # Retrieve the database
    mc = get_db()
    # Get the nodes from it
    if pagination:
        LD_nodes = list(
            mc["nodes"].find(mongodb_filter).skip(pagination[0]).limit(pagination[1])
        )
    else:
        LD_nodes = list(mc["nodes"].find(mongodb_filter))
    # Return the retrieved nodes
    return LD_nodes


def strip_artificial_fields_from_node(D_node):
    # Returns a copy. Does not mutate the original.
    # Useful because mongodb puts a non-json-serializable "_id" field.
    fields_to_remove = ["_id"]
    return dict((k, v) for (k, v) in D_node.items() if k not in fields_to_remove)
