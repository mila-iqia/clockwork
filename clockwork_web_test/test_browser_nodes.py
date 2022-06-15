"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import json
import pytest

from clockwork_web.core.pagination_helper import get_pagination_values


def test_nodes(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the nodes are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    response = client.get("/nodes/list")
    for i in range(0, 40):  # TODO: centralize this value
        D_node = fake_data["nodes"][i]
        assert D_node["slurm"]["name"].encode("utf-8") in response.data


@pytest.mark.parametrize(
    "num_page,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_nodes_with_both_pagination_options(
    client, fake_data: dict[list[dict]], num_page, nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated when using both pagination options: num_page and nbr_items_per_page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        num_page            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Get the response
    response = client.get("/nodes/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, num_page, nbr_items_per_page
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_node = fake_data["nodes"][i]
            assert D_node["slurm"]["name"].encode("utf-8") in response.data


@pytest.mark.parametrize("num_page", [1, 2, 3, "lala", 7.8, False])
def test_nodes_with_num_page_pagination_option(
    client, fake_data: dict[list[dict]], num_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the num_page pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        num_page            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Get the response
    response = client.get("/nodes/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, num_page, None
    )
    # Assert that the retrieved nodes correspond to the expected nodes

    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_node = fake_data["nodes"][i]
            assert D_node["slurm"]["name"].encode("utf-8") in response.data


@pytest.mark.parametrize("nbr_items_per_page", [1, 29, 50, -1, [1, 2], True])
def test_nodes_with_num_page_pagination_option(
    client, fake_data: dict[list[dict]], nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the num_page pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Get the response
    response = client.get("/nodes/list?num_page={}&nbr_items_per_page={}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, None, nbr_items_per_page
    )
    # Assert that the retrieved nodes correspond to the expected nodes

    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(fake_data):
            D_node = fake_data["nodes"][i]
            assert D_node["slurm"]["name"].encode("utf-8") in response.data


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth")
)
def test_nodes_with_filter(client, fake_data: dict[list[dict]], cluster_name):
    """
    Same as `test_nodes` but adding a filter for the key "cluster_name".
    This tests the encoding of args with the ?k1=v1&k2=v2 notation in the url.
    """

    # Yes, "sephiroth" is a fake cluster name. There are no entries in the data for it.

    response = client.get(f"/nodes/list?cluster_name={cluster_name}")

    for D_node in fake_data["nodes"]:
        if D_node["slurm"]["cluster_name"] == cluster_name:
            assert D_node["slurm"]["name"].encode("utf-8") in response.data
        else:
            # We're being a little demanding here by asking that the name of the
            # host should never occur in the document. The host names are unique,
            # but there's no reason or guarantee that a string like "cn-a003" should NEVER
            # show up elsewhere in the page for some other reason.
            # This causes issues when the fake data had node names that were all "machine"
            # with some integer.
            assert D_node["slurm"]["name"].encode("utf-8") not in response.data


def test_single_node(client, fake_data):
    node = fake_data["nodes"][0]["slurm"]
    response = client.get(
        f"/nodes/one?node_name={node['name']}&cluster_name={node['cluster_name']}"
    )
    assert response.status_code == 200
    assert node["alloc_tres"].encode("ascii") in response.data


def test_single_node_not_found(client):
    response = client.get("/nodes/one?node_name=patate009")
    assert response.status_code == 400


def test_single_node_cluster_only(client):
    response = client.get("/nodes/one?cluster_name=mila")
    assert response.status_code == 400
