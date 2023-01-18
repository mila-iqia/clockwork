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
from clockwork_web.core.users_helper import get_default_setting_value


def test_nodes(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the nodes are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Request the nodes list
    response = client.get("/nodes/list")

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        fake_data["nodes"],
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    for i in range(0, get_default_setting_value("nbr_items_per_page")):
        D_node = sorted_all_nodes[i]
        assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, 10), (0, 22), ("blbl", 30), (True, 5), (3, 14)]
)
def test_nodes_with_both_pagination_options(
    client, fake_data: dict[list[dict]], page_num, nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated when using both pagination options: page_num and nbr_items_per_page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(
        f"/nodes/list?page_num={page_num}&nbr_items_per_page={nbr_items_per_page}"
    )

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, nbr_items_per_page
    )

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        fake_data["nodes"],
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize("page_num", [1, 2, 3, "lala", 7.8, False])
def test_nodes_with_page_num_pagination_option(
    client, fake_data: dict[list[dict]], page_num
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the page_num pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(f"/nodes/list?page_num={page_num}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, None
    )

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        fake_data["nodes"],
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize("nbr_items_per_page", [1, 29, 50, -1, [1, 2], True])
def test_nodes_with_page_num_pagination_option(
    client, fake_data: dict[list[dict]], nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the page_num pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(f"/nodes/list?nbr_items_per_page={nbr_items_per_page}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, None, nbr_items_per_page
    )

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        fake_data["nodes"],
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(number_of_skipped_items, nbr_items_per_page):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth")
)
def test_nodes_with_filter(client, fake_data: dict[list[dict]], cluster_name):
    """
    Same as `test_nodes` but adding a filter for the key "cluster_name".
    This tests the encoding of args with the ?k1=v1&k2=v2 notation in the url.
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Yes, "sephiroth" is a fake cluster name. There are no entries in the data for it.

    # We use `nbr_items_per_page=1000000` to avoid a situation where the expected result
    # ends up on the second or later page. Not 100% sure that this is necessary,
    # but it certainly takes care a situation where this test failed because nodes
    # were missing from the response.

    response = client.get(
        f"/nodes/list?cluster_name={cluster_name}&nbr_items_per_page=1000000"
    )

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        fake_data["nodes"],
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    for D_node in sorted_all_nodes:
        if D_node["slurm"]["cluster_name"] == cluster_name:
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            # We're being a little demanding here by asking that the name of the
            # host should never occur in the document. The host names are unique,
            # but there's no reason or guarantee that a string like "cn-a003" should NEVER
            # show up elsewhere in the page for some other reason.
            # This causes issues when the fake data had node names that were all "machine"
            # with some integer.
            assert D_node["slurm"]["name"] not in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node(client, fake_data):

    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    node = fake_data["nodes"][0]["slurm"]
    response = client.get(
        f"/nodes/one?node_name={node['name']}&cluster_name={node['cluster_name']}"
    )
    assert response.status_code == 200
    assert node["alloc_tres"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_not_found(client):
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    response = client.get("/nodes/one?node_name=patate009")
    assert response.status_code == 400

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_cluster_only(client):
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    response = client.get("/nodes/one?cluster_name=mila")
    assert response.status_code == 400

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
