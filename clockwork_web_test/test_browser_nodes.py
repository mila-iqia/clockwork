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
from clockwork_web.core.users_helper import (
    get_available_clusters_from_db,
    get_default_setting_value,
)


def _get_associated_nodes_from_fake_data_in_order(current_user_id, fake_data):
    """
    There were 5 copies of this exact code.
    This is a way to avoid redundancy and simplify reading.

    This function simply returns the nodes in the fake_data
    that pertain to the current user. It is used to determine
    the ground truth for many tests.

    Returns a sorted list of nodes.
    """

    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access

    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the expected nodes by name, then cluster name
    return sorted(
        expected_nodes,
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )


@pytest.mark.parametrize(
    "current_user_id",
    (
        "student00@mila.quebec",  # Can access all clusters
        "student06@mila.quebec",  # Can only access Mila cluster
    ),
)
def test_nodes(client, fake_data: dict[list[dict]], current_user_id):
    """
    Check that all the names of the nodes are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.

    Parameters:
    client              The web client to request. Note that this fixture
                        depends on other fixtures that are going to put the
                        fake data in the database for us
    fake_data           The data our tests are based on
    current_user_id     ID of the user requesting the nodes
    """
    # Log in to Clockwork as the current_user (provided as parameter)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Request the nodes list
    response = client.get("/nodes/list")

    expected_nodes = _get_associated_nodes_from_fake_data_in_order(
        current_user_id, fake_data
    )

    # Check if all the expected nodes are contained in the response
    # These are the X first nodes of the nodes list (X being the
    # number of items to display per page the user has set)
    for D_node in expected_nodes[0 : get_default_setting_value("nbr_items_per_page")]:
        assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_nodes_without_all_access(client, fake_data: dict[list[dict]]):
    """
    Check that only the expected subset of nodes is returned in the HTML generated
    by the call of /node/list when we are connected as a user who does not have
    access to all the clusters.
    """
    # Initialization
    current_user_id = (
        "student06@mila.quebec"  # student06 has only access to the Mila cluster
    )
    available_clusters_for_the_user = ["mila"]

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Request the nodes list
    response = client.get("/nodes/list")

    expected_nodes = _get_associated_nodes_from_fake_data_in_order(
        current_user_id, fake_data
    )
    for D_node in expected_nodes:
        # As the student06 has only access to the Mila cluster
        assert D_node["slurm"]["cluster_name"] == "mila"

    # Check if only the expected nodes are contained in the response
    # and the unexpected nodes are not.
    for D_node in fake_data["nodes"]:
        if D_node in expected_nodes:
            # Check if expected nodes are returned
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            # Check if unexpected nodes are not returned
            assert D_node["slurm"]["name"] not in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "current_user_id,page_num,nbr_items_per_page",
    [
        ("student00@mila.quebec", 1, 10),  # student00 can access all clusters
        ("student06@mila.quebec", 1, 16),  # student06 can only access Mila cluster
        ("student00@mila.quebec", 0, 22),  # student00 can access all clusters
        ("student00@mila.quebec", "blbl", 30),
        # As the provided value is incorrect, the page_num is set to 1 by default
        # student00 can access all clusters
        ("student00@mila.quebec", True, 5),
        # As the provided value is incorrect, the page_num is set to 1 by default
        # student06 can only access Mila cluster
        ("student06@mila.quebec", 3, 14),  # student06 can only access Mila cluster
    ],
)
def test_nodes_with_both_pagination_options(
    client, fake_data: dict[list[dict]], current_user_id, page_num, nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated when using both pagination options: page_num and nbr_items_per_page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        current_user_id     ID of the user requesting the nodes
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Log in to Clockwork as the current_user (provided as parameter)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response of the request we are testing
    response = client.get(
        f"/nodes/list?page_num={page_num}&nbr_items_per_page={nbr_items_per_page}"
    )

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, page_num, nbr_items_per_page
    )

    expected_nodes = _get_associated_nodes_from_fake_data_in_order(
        current_user_id, fake_data
    )

    # From it, retrieve the expected nodes regarding the pagination options
    expected_nodes = expected_nodes[
        number_of_skipped_items : number_of_skipped_items + nbr_items_per_page
    ]

    # Check if only the expected nodes are contained in the response and the unexpected nodes aren't
    for D_node in fake_data["nodes"]:
        if D_node in expected_nodes:
            # Check if expected nodes are returned
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            # Check if unexpected nodes are not returned
            assert D_node["slurm"]["name"] not in response.get_data(as_text=True)
    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "current_user_id,page_num",
    [
        (
            "student00@mila.quebec",
            1,
        ),  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
        (
            "student06@mila.quebec",
            3,
        ),  # student06 can only access Mila cluster and his/her nbr_items_per_page preference is set to 40
        (
            "student00@mila.quebec",
            "lala",
        ),  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
        (
            "student06@mila.quebec",
            7.8,
        ),  # student06 can only access Mila cluster and his/her nbr_items_per_page preference is set to 40
        (
            "student00@mila.quebec",
            False,
        ),  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
    ],
)
def test_nodes_with_page_num_pagination_option(
    client, fake_data: dict[list[dict]], current_user_id, page_num
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the page_num pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        current_user_id     ID of the user requesting the nodes
        page_num            The number of the page displaying the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Log in to Clockwork as the current_user (provided as parameter)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(f"/nodes/list?page_num={page_num}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, page_num, None
    )

    expected_nodes = _get_associated_nodes_from_fake_data_in_order(
        current_user_id, fake_data
    )

    # From it, retrieve the expected nodes regarding the pagination options
    expected_nodes = expected_nodes[
        number_of_skipped_items : number_of_skipped_items + nbr_items_per_page
    ]

    # Check if only the expected nodes are contained in the response and the unexpected nodes aren't
    for D_node in fake_data["nodes"]:
        if D_node in expected_nodes:
            # Check if expected nodes are returned
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            # Check if unexpected nodes are not returned
            assert D_node["slurm"]["name"] not in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "current_user_id, nbr_items_per_page",
    [
        ("student00@mila.quebec", 1),  # student00 can access all clusters
        ("student06@mila.quebec", 29),  # student06 can only access Mila cluster
        ("student00@mila.quebec", 50),  # student00 can access all clusters
        ("student06@mila.quebec", -1),  # student06 can only access Mila cluster
        ("student00@mila.quebec", [1, 2]),  # student00 can access all clusters
        ("student06@mila.quebec", True),  # student06 can only access Mila cluster
    ],
)
def test_nodes_with_nbr_items_per_page_pagination_option(
    client, fake_data: dict[list[dict]], current_user_id, nbr_items_per_page
):
    """
    Check that all the expected names of the nodes are present in the HTML
    generated using only the nbr_items_per_page pagination option.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        current_user_id     ID of the user requesting the nodes
        nbr_items_per_page  The number of nodes we want to display per page
    """
    # Log in to Clockwork as the current_user (provided as parameter)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(f"/nodes/list?nbr_items_per_page={nbr_items_per_page}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        current_user_id, None, nbr_items_per_page
    )

    expected_nodes = _get_associated_nodes_from_fake_data_in_order(
        current_user_id, fake_data
    )
    # Then keep only the expected nodes based on the pagination options
    expected_nodes = expected_nodes[
        number_of_skipped_items : (number_of_skipped_items + nbr_items_per_page)
    ]

    # Check if only the expected nodes are contained in the response
    # and the unexpected nodes are not.
    for D_node in fake_data["nodes"]:
        if D_node in expected_nodes:
            # Check if expected nodes are returned
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            # Check if unexpected nodes are not returned
            assert D_node["slurm"]["name"] not in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "current_user_id,cluster_name",
    [
        ("student00@mila.quebec", "mila"),  # student00 can access to the cluster "mila"
        ("student06@mila.quebec", "mila"),  # student06 can access to the cluster "mila"
        (
            "student00@mila.quebec",
            "cedar",
        ),  # student00 can access to the cluster "cedar"
        (
            "student06@mila.quebec",
            "graham",
        ),  # student06 can not access to the cluster "graham"
        (
            "student00@mila.quebec",
            "beluga",
        ),  # student00 can access to the cluster "beluga"
        (
            "student00@mila.quebec",
            "sephiroth",
        ),  # the cluster "sephiroth" does not exist
    ],
)
def test_nodes_with_filter(
    client, fake_data: dict[list[dict]], current_user_id, cluster_name
):
    """
    Same as `test_nodes` but adding a filter for the key "cluster_name".
    This tests the encoding of args with the ?k1=v1&k2=v2 notation in the url.

    Parameters:
    client              The web client to request. Note that this fixture
                        depends on other fixtures that are going to put the
                        fake data in the database for us
    fake_data           The data our tests are based on
    current_user_id     ID of the user requesting the nodes
    cluster_name        The name of the cluster used as filter to the nodes
    """
    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Yes, "sephiroth" is a fake cluster name. There are no entries in the data for it.

    # We use `nbr_items_per_page=1000000` to avoid a situation where the expected result
    # ends up on the second or later page. Not 100% sure that this is necessary,
    # but it certainly takes care a situation where this test failed because nodes
    # were missing from the response.

    # Log in to Clockwork as the current_user (provided as parameter)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response of the request we are testing
    response = client.get(
        f"/nodes/list?cluster_name={cluster_name}&nbr_items_per_page=1000000"
    )

    # Retrieve all the nodes from the fake data
    all_nodes = fake_data["nodes"]

    if cluster_name not in get_available_clusters_from_db(current_user_id):
        # If the cluster name is not in the clusters available for the user,
        # all the available nodes from all the clusters are returned
        expected_nodes = _get_associated_nodes_from_fake_data_in_order(  # These are all the nodes available for the user
            current_user_id, fake_data
        )
    else:
        # If the cluster name is in the clusters available for the user,
        # only the nodes related to this cluster should be displayed
        expected_nodes = [
            D_node
            for D_node in all_nodes
            if D_node["slurm"]["cluster_name"] == cluster_name
        ]

    for D_node in all_nodes:
        if D_node in expected_nodes:
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)
        else:
            assert (
                f"&cluster_name={D_node['slurm']['cluster_name']}"
                not in response.get_data(as_text=True)
            )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node(client, fake_data):

    """
    Check the function route_one when success (ie an authenticated user
    request an existing node to which he/she has access).

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """

    # Log in to Clockwork as student00 (who can access all clusters)
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    node = fake_data["nodes"][1]["slurm"]
    response = client.get(
        f"/nodes/one?node_name={node['name']}&cluster_name={node['cluster_name']}"
    )

    # Check the response
    assert response.status_code == 200
    assert (
        node["tres_used"] is not None
    )  # tres_used could be None for a node, we just don't want this case for the current test
    assert node["tres_used"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_not_found_node_name_only(client):
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # Launch the request without providing a cluster name
    response = client.get("/nodes/one?node_name=patate009")

    # Assert that a 400 Error is returned
    assert response.status_code == 404

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_not_found_on_available_cluster(client):
    """
    Check the function route_one for a connected user who request an
    unexisting node.

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    response = client.get("/nodes/one?node_name=patate009&cluster_name=mila")
    assert response.status_code == 404  # Not found

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_not_found(client, fake_data):
    """
    Check the function route_one for a connected user who request a node
    on a cluster he/she has no access to.

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """
    # Initialization
    current_user_id = (
        "student06@mila.quebec"  # student06 has only access to Mila cluster
    )

    # Retrieve the first node on a cluster which is not the Mila one
    for D_node in fake_data["nodes"]:
        if D_node["slurm"]["cluster_name"] != "mila":
            node_name = D_node["slurm"]["name"]
            cluster_name = D_node["slurm"]["cluster_name"]
            break

    assert node_name is not None  # However, the test has no point

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    response = client.get(
        f"/nodes/one?node_name={node_name}&cluster_name={cluster_name}"
    )
    assert response.status_code == 404  # Not found

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_cluster_only(client):

    """
    Check the function route_one when only the cluster is provided.

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
    """
    # Initialization
    current_user_id = (
        "student00@mila.quebec"  # student00 has access to the Mila and DRAC clusters
    )

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Launch the request without providing a node name
    response = client.get("/nodes/one?cluster_name=mila")

    # Assert that a 400 Error is returned
    assert response.status_code == 400

    # Might as well check that the error message is the one we expect.
    # 'The parameter &#34;node_name&#34; has not been provided.'
    assert 'The parameter &#34;node_name&#34; has not been provided.' in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
