"""
Tests fort the clockwork_web.core.nodes_helper functions.
"""

import pytest

from clockwork_web.core.nodes_helper import *
from clockwork_web.db import get_db
from clockwork_web.core.pagination_helper import get_pagination_values


def test_get_nodes_without_filters_or_pagination(app, fake_data):
    """
    Test the function get_nodes when it lists all the nodes.

    Parameters:
        app         The scope of our tests, used to set the context (to access MongoDB)
        fake_data   The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Retrieve the nodes we want to list
        LD_retrieved_nodes = get_nodes()

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Assert that they correspond to the nodes we expect
        assert LD_retrieved_nodes == fake_data["nodes"]


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_get_nodes_with_pagination(app, fake_data, page_num, nbr_items_per_page):
    """
    Test the function get_nodes by providing only pagination parameters.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        pagination_parameters = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Retrieve the nodes we want to list
        LD_retrieved_nodes = get_nodes(pagination=pagination_parameters)

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Retrieve the bounds of the interval of index in which the expected
        # nodes are contained
        (nbr_of_skipped_items, nbr_displayed_items_per_page) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Assert that they correspond to the nodes we expect
        assert (
            LD_retrieved_nodes
            == fake_data["nodes"][
                nbr_of_skipped_items : nbr_of_skipped_items
                + nbr_displayed_items_per_page
            ]
        )
