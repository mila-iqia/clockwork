import pytest


@pytest.mark.parametrize("cluster_name", ["mila", "graham"])
def test_clusters_one_success(client, cluster_name):
    """
    Test the function route_one when retrieving an existing cluster.

    Parameters:
    - client        The web client used to send the request
    - cluster_name  Name of the cluster we want to find
    """
    # Retrieve the response to the call we are testing
    response = client.get("/clusters/one?cluster_name={}".format(cluster_name))

    # Check if the response is the expected one
    assert response.status_code == 200  # Success


def test_clusters_one_not_found(client):
    """
    Test the function route_one when trying to retrieve an inexisting cluster.

    Parameters:
    - client        The web client used to send the request
    """
    # Set an inexisting cluster name
    inexisting_cluster_name = "idonotexist"

    # Retrieve the response to the call we are testing
    response = client.get(
        "/clusters/one?cluster_name={}".format(inexisting_cluster_name)
    )

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
    assert b"The argument cluster_name is missing." in response.data
