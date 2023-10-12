"""
Tests fort the clockwork_web.browser_routes.users functions.
"""
import pytest


def test_users_one_success(client, fake_data):
    """
    Test the function route_one when retrieving an existing user.

    Parameters:
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    """
    # Check that the fake_data provide users (otherwise, the tests are pointless)
    assert "users" in fake_data
    assert len(fake_data["users"]) > 0

    # Retrieve the name of an existing user from the fake_data
    user = fake_data["users"][0]
    username = user["mila_email_username"]

    # Retrieve the response to the call we are testing
    response = client.get("/users/one?username={}".format(username))

    # Check if the response is the expected one
    assert response.status_code == 200  # Success
    if user["mila_account_username"]:
        assert "{}".format(user["mila_account_username"]) in response.get_data(
            as_text=True
        )
    if user["cc_account_username"]:
        assert "{}".format(user["cc_account_username"]) in response.get_data(
            as_text=True
        )


def test_users_one_username_not_found(client):
    """
    Test the function route_one when trying to retrieve an inexisting user.

    Parameters:
    - client    The web client used to send the request
    """
    # Define the name of an inexisting user
    username = "thisisnottheuseryourelookingfor"

    # Retrieve the response to the call we are testing
    response = client.get("/users/one?username={}".format(username))

    # Check if the response is the expected one
    assert response.status_code == 404  # Not Found
    assert "The requested user has not been found." in response.get_data(as_text=True)


def test_users_one_missing_username(client):
    """
    Test the function route_one when we do not provide the username argument.

    Parameters:
    - client    The web client used to send the request
    """
    # Retrieve the response to the call we are testing
    response = client.get("/users/one?")

    # Check if the response is the expected one
    assert response.status_code == 400  # Bad Request
    assert "Missing argument username." in response.get_data(as_text=True)
