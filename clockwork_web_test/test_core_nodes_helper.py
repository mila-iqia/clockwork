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
        (LD_retrieved_nodes, nodes_count) = get_nodes()

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Assert that they correspond to the nodes we expect
        assert LD_retrieved_nodes == fake_data["nodes"]
        assert nodes_count == None


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
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Retrieve the nodes we want to list
        (LD_retrieved_nodes, nodes_count) = get_nodes(
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
        )

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Assert that they correspond to the nodes we expect
        assert (
            LD_retrieved_nodes
            == fake_data["nodes"][
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )
        assert nodes_count == None


def test_get_and_count_nodes_without_filters_or_pagination(app, fake_data):
    """
    Test the function get_nodes when count is True and all the nodes are requested.

    Parameters:
        app         The scope of our tests, used to set the context (to access MongoDB)
        fake_data   The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Retrieve the nodes we want to list
        (LD_retrieved_nodes, nbr_total_nodes) = get_nodes(count=True)

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Assert that they correspond to the nodes we expect
        assert LD_retrieved_nodes == fake_data["nodes"]

        # Assert that the number nbr_total_nodes correspond to the filters without pagination
        # Here, we do not use filter nor pagination. Thus, this number should be the number of nodes
        assert nbr_total_nodes == len(fake_data["nodes"])


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_get_and_count_nodes_with_pagination(
    app, fake_data, page_num, nbr_items_per_page
):
    """
    Test the function get_nodes when count is True, and when providing only pagination parameters.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Retrieve the nodes we want to list
        (LD_retrieved_nodes, nbr_total_nodes) = get_nodes(
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
            count=True,
        )

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Assert that they correspond to the nodes we expect
        assert (
            LD_retrieved_nodes
            == fake_data["nodes"][
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )

        # Assert that the retrieved number correspond to the expected number of nodes
        # Here, we only apply pagination and not filters, so that the expected number
        # is the total of nodes in the database
        assert nbr_total_nodes == len(fake_data["nodes"])


# ---------------------


@pytest.mark.parametrize("page_num, nbr_items_per_page", [(1, 10), (3, 2)])
def test_get_and_count_nodes_by_cluster_name_with_pagination(
    app, fake_data, page_num, nbr_items_per_page
):
    """
    Test the function get_nodes when looking for the nodes of a specific cluster and when count is True.

    Parameters:
        app                 The scope of our tests, used to set the context (to access MongoDB)
        fake_data           The data on which our tests are based
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Use the app context
    with app.app_context():
        # Define the pagination parameters
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            None, page_num, nbr_items_per_page
        )

        # Set up the filter applied in this test
        cluster_name = "mila"
        filter = {"slurm.cluster_name": cluster_name}

        # Retrieve the nodes we want to list
        (LD_retrieved_nodes, nbr_total_nodes) = get_nodes(
            mongodb_filter=filter,
            nbr_skipped_items=nbr_skipped_items,
            nbr_items_to_display=nbr_items_to_display,
            count=True,
        )

        # Withdraw the "_id" element of the retrieved nodes
        LD_retrieved_nodes = [
            strip_artificial_fields_from_node(D_node) for D_node in LD_retrieved_nodes
        ]

        # Retrieve the expected nodes
        LD_expected_nodes = []
        for D_node in fake_data["nodes"]:
            if D_node["slurm"]["cluster_name"] == cluster_name:
                LD_expected_nodes.append(D_node)

        # Assert that they correspond to the nodes we expect
        assert (
            LD_retrieved_nodes
            == LD_expected_nodes[
                nbr_skipped_items : nbr_skipped_items + nbr_items_to_display
            ]
        )

        # Assert that the retrieved number correspond to the number of expected nodes
        # before applying the pagination
        assert nbr_total_nodes == len(LD_expected_nodes)
