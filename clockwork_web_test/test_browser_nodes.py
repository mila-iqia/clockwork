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

    # Get the response of the request we are testing
    response = client.get("/nodes/list")

    # Filter the nodes contained in the fake data regarding the current user
    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access
    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the expected nodes by name, then cluster name
    sorted_all_nodes = sorted(
        expected_nodes,
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the expected nodes are retrieved
    for i in range(
        0, min(get_default_setting_value("nbr_items_per_page"), len(sorted_all_nodes))
    ):
        D_node = sorted_all_nodes[i]
        assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page,current_user_id",
    [
        (1, 10, "student00@mila.quebec"),  # student00 can access all clusters
        (1, 16, "student06@mila.quebec"),  # student06 can only access Mila cluster
        (0, 22, "student00@mila.quebec"),  # student00 can access all clusters
        ("blbl", 30, "student00@mila.quebec"),
        # As the provided value is incorrect, the page_num is set to 1 by default
        # student00 can access all clusters
        (True, 5, "student00@mila.quebec"),
        # As the provided value is incorrect, the page_num is set to 1 by default
        # student06 can only access Mila cluster
        (3, 14, "student00@mila.quebec"),  # student06 can only access Mila cluster
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
        None, page_num, nbr_items_per_page
    )

    # Filter the nodes contained in the fake data regarding the current user
    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access
    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the nodes contained in the fake data by name, then cluster name
    sorted_all_nodes = sorted(
        expected_nodes,
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(
        number_of_skipped_items,
        min(number_of_skipped_items + nbr_items_per_page, len(sorted_all_nodes)),
    ):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "page_num,current_user_id",
    [
        (
            1,
            "student00@mila.quebec",
        ),  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
        (
            3,
            "student06@mila.quebec",
        ),  # student06 can only access Mila cluster and his/her nbr_items_per_page preference is set to 40
        (
            "lala",
            "student00@mila.quebec",
        ),  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
        (
            7.8,
            "student06@mila.quebec",
        ),  # student06 can only access Mila cluster and his/her nbr_items_per_page preference is set to 40
        (False, "student00@mila.quebec"),
    ],
)  # student00 can access all clusters and his/her nbr_items_per_page preference is set to 40
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

    # Get the response of the request we are testing
    response = client.get(f"/nodes/list?page_num={page_num}")

    # Retrieve the bounds of the interval of index in which the expected nodes
    # are contained
    (number_of_skipped_items, nbr_items_per_page) = get_pagination_values(
        None, page_num, None
    )

    # Filter the nodes contained in the fake data regarding the current user
    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access
    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the expected nodes by name, then cluster name
    sorted_all_nodes = sorted(
        expected_nodes,
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(
        number_of_skipped_items,
        min(number_of_skipped_items + nbr_items_per_page, len(sorted_all_nodes)),
    ):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


@pytest.mark.parametrize(
    "nbr_items_per_page, current_user_id",
    [
        (1, "student00@mila.quebec"),  # student00 can access all clusters
        (29, "student06@mila.quebec"),  # student06 can only access Mila cluster
        (50, "student00@mila.quebec"),  # student00 can access all clusters
        (-1, "student06@mila.quebec"),  # student06 can only access Mila cluster
        ([1, 2], "student00@mila.quebec"),  # student00 can access all clusters
        (True, "student06@mila.quebec"),  # student06 can only access Mila cluster
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
        None, None, nbr_items_per_page
    )

    # Filter the nodes contained in the fake data regarding the current user
    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access
    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the expected nodes by name, then cluster name
    sorted_all_nodes = sorted(
        expected_nodes,
        key=lambda d: (d["slurm"]["name"], d["slurm"]["cluster_name"]),
    )

    # Assert that the retrieved nodes correspond to the expected nodes
    for i in range(
        number_of_skipped_items,
        min(number_of_skipped_items + nbr_items_per_page, len(sorted_all_nodes)),
    ):
        if i < len(sorted_all_nodes):
            D_node = sorted_all_nodes[i]
            assert D_node["slurm"]["name"] in response.get_data(as_text=True)

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

    # Filter the nodes contained in the fake data regarding the current user
    user_clusters = get_available_clusters_from_db(
        current_user_id
    )  # Retrieve the clusters the current user can access
    expected_nodes = [
        node
        for node in fake_data["nodes"]
        if node["slurm"]["cluster_name"] in user_clusters
    ]

    # Sort the expected nodes by name, then cluster name
    sorted_all_nodes = sorted(
        expected_nodes,
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
            assert (
                f"/nodes/one?node_name={D_node['slurm']['name']}&cluster_name={cluster_name}"
                not in response.get_data(as_text=True)
            )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node(client, fake_data):
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # Retrieve the first node of the fake data
    node = fake_data["nodes"][0]["slurm"]
    response = client.get(
        f"/nodes/one?node_name={node['name']}&cluster_name={node['cluster_name']}"
    )

    # Check the response
    assert response.status_code == 200
    assert node["alloc_tres"] in response.get_data(as_text=True)

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_node_name_only(client):
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # Launch the request without providing a cluster name
    response = client.get("/nodes/one?node_name=patate009")

    # Assert that a 400 Error is returned
    assert response.status_code == 400

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_single_node_cluster_only(client):
    # Log in to Clockwork as student00 (who can access all clusters)
    login_response = client.get("/login/testing?user_id=student00@mila.quebec")
    assert login_response.status_code == 302  # Redirect

    # Launch the request without providing a node name
    response = client.get("/nodes/one?cluster_name=mila")

    # Assert that a 400 Error is returned
    assert response.status_code == 400

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
