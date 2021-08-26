
"""
Functions in this file are things that are called after the authentication step.
They don't do any authentication themselves, but are serving the browser_routes
and rest_routes, which are just fronts for these functions here.
"""

from flask.globals import current_app
from clockwork_web.db import get_db
# from clockwork_web.core.jobs_helper import get_filter_cluster_name

def get_filter_name(name):
    """
    Looks rather useless right now, but this is where you'd patch
    some modifications the "name" if you want to have them.
    Things like tolower() or stripping spaces.
    """
    if name is None:
        return {}
    else:
        return {"name": name}

def get_nodes(mongodb_filter:dict={}) -> list[dict]:
    """
    Talk to the database and get the information.

    Returns a list of dict with the properties of nodes.
    """
    mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    LD_nodes = list(mc["nodes"].find(mongodb_filter))
    return [strip_artificial_fields_from_node(D_node) for D_node in LD_nodes]


def strip_artificial_fields_from_node(D_node):
    # Returns a copy. Does not mutate the original.
    # Useful because mongodb puts a non-json-serializable "_id" field.
    fields_to_remove = ["_id"] #, "grafana_helpers"]
    return dict( (k, v) for (k, v) in D_node.items() if k not in fields_to_remove)