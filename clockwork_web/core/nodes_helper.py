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


def get_nodes(
    mongodb_filter: dict = {},
    nbr_skipped_items=None,
    nbr_items_to_display=None,
    want_count=False,
) -> list:
    """
    Talk to the database and get the information.

    Parameters:
        mongodb_filter          A concatenation of the filters to apply in order
                                to select the nodes we want to retrieve from the
                                MongoDB database
        nbr_skipped_items       Number of elements to skip while listing the nodess
        nbr_items_to_display    Number of nodes to display
        want_count              Whether or not we are interested by the number of
                                unpaginated nodes.

    Returns:
        Returns a tuple (nodes_list, nodes_count or None).
        The first element is a list of dictionaries with the properties of the listed nodes.
        In general we expect len(nodes_list) to be nbr_items_to_display if
        we found sufficiently many matches.

        The second element contains the total number nodes of found with the mongodb_filter,
        counting the whole database and not just one page. It is None if want_count is False.

    """
    # Assert that the two pagination elements (nbr_skipped_items and
    # nbr_items_to_display) are respectively positive and strictly positive
    # integers
    if not (type(nbr_skipped_items) == int and nbr_skipped_items >= 0):
        nbr_skipped_items = None

    if not (type(nbr_items_to_display) == int and nbr_items_to_display > 0):
        nbr_items_to_display = None

    # Retrieve the database
    mc = get_db()

    # Get the filtered and paginated nodes from it
    if nbr_skipped_items != None and nbr_items_to_display:
        LD_nodes = list(
            mc["nodes"]
            .find(mongodb_filter)
            .sort([["slurm.name", 1], ["slurm.cluster_name", 1]])
            .skip(nbr_skipped_items)
            .limit(nbr_items_to_display)
        )
    else:
        LD_nodes = list(
            mc["nodes"]
            .find(mongodb_filter)
            .sort([["slurm.name", 1], ["slurm.cluster_name", 1]])
        )

    if want_count:
        # Get the number of filtered nodes (not paginated)
        nbr_total_nodes = mc["nodes"].count_documents(mongodb_filter)
    else:
        # If want_count is False, nbr_total_nodes is None
        nbr_total_nodes = None

    # Return the retrieved nodes and the number of unpagined nodes
    return (LD_nodes, nbr_total_nodes)


def strip_artificial_fields_from_node(D_node):
    # Returns a copy. Does not mutate the original.
    # Useful because mongodb puts a non-json-serializable "_id" field.
    fields_to_remove = ["_id"]
    return dict((k, v) for (k, v) in D_node.items() if k not in fields_to_remove)
