import pytest


@pytest.mark.parametrize(
    "current_user_id,cluster_name",
    [
        (
            "student00@mila.quebec",
            "mila",
        ),  # student00 can access Mila and all DRAC clusters
        (
            "student00@mila.quebec",
            "graham",
        ),  # student00 can access Mila and all DRAC clusters
        (
            "student06@mila.quebec",
            "mila",
        ),  # student06 can only access to the Mila cluster
    ],
)
def test_clusters_one_success(client, current_user_id, cluster_name):
    """
    Test the function route_one when retrieving an existing cluster.

    Parameters:
    - client            The web client used to send the request
    - current_user_id   ID of the user requested the node information
    - cluster_name      Name of the cluster we want to find
    """
    # Log in to Clockwork as a specific user (provided by the function parameters)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Retrieve the response to the call we are testing
    response = client.get(f"/clusters/one?cluster_name={cluster_name}")

    # Check if the response is the expected one
    assert response.status_code == 200  # Success

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_clusters_one_forbidden(client):
    """
    Test the function route_one when retrieving an existing cluster, to which
    the current user does not have access.

    Parameters:
    - client            The web client used to send the request
    """
    # Initialization
    current_user_id = (
        "student06@mila.quebec"  # student06 has access only to the Mila cluster
    )
    cluster_name = "graham"  # ... thus, student06 should not have access to it

    # Log in to Clockwork as a specific user (provided by the function parameters)
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    # Retrieve the response to the call we are testing
    response = client.get(f"/clusters/one?cluster_name={cluster_name}")

    # Check if the response is the expected one
    assert response.status_code == 403  # Forbidden

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_clusters_one_not_found(client):
    """
    Test the function route_one when trying to retrieve an inexisting cluster.

    Parameters:
    - client        The web client used to send the request
    """
    # Set an inexisting cluster name
    inexisting_cluster_name = "idonotexist"

    # Retrieve the response to the call we are testing
    response = client.get(f"/clusters/one?cluster_name={inexisting_cluster_name}")

    # Check if the response is the expected one
    assert response.status_code == 404  # Not Found


def test_clusters_one_no_cluster_name_provided(client):
    """
    Test the functionroute_one when providing no cluster_name.


    - client        The web client used to send the request
    """
    # Retrieve the response to the call we are testing
    response = client.get("/clusters/one")

    # Check if the response is the expected one
    assert response.status_code == 400  # Bad Request

    # Assert that the expected error message is in the page
    assert "The argument cluster_name is missing." in response.get_data(as_text=True)
