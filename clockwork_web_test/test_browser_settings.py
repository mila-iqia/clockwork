from flask_login import current_user
import pytest

from clockwork_web.db import get_db


def test_settings_index(client):
    response = client.get("/settings/")

    assert current_user.clockwork_api_key.encode("ascii") in response.data


def test_settings_new_key(client):
    # This is to establish a 'current_user'
    client.get("/settings/")

    api_key = current_user.clockwork_api_key

    response = client.get("/settings/new_key")

    assert current_user.clockwork_api_key != api_key

    assert response.status_code == 302
    assert response.headers["Location"] == "/settings/"


def test_settings_set_nbr_items_per_page_missing_argument(client):
    """
    Test the function route_set_nbr_items_per_page without sending a
    nbr_items_per_page as argument.

    Parameters:
    - client    The web client used to send the request
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Retrieve the response to the call we are testing
    response = client.get("/settings/web/nbr_items_per_page/set")

    # Check if the response is the expected one
    assert response.status_code == 400


@pytest.mark.parametrize("nbr_items_per_page", ["test", 1.3, True])
def test_settings_set_nbr_items_per_page_wrong_type(client, nbr_items_per_page):
    """
    Test the function route_set_nbr_items_per_page when sending the wrong type
    for nbr_items_per_page.

    Parameters:
    - client                The web client used to send the request
    - nbr_items_per_page    The value to try to set as the preferred number of
                            items to display per page for the current user
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    test_request = "/settings/web/nbr_items_per_page/set?nbr_items_per_page={}".format(
        nbr_items_per_page
    )

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400


@pytest.mark.parametrize("nbr_items_per_page", [-20, -5, 0])
def test_settings_set_nbr_items_per_page_zero_or_negative_value(
    client, nbr_items_per_page
):
    """
    Test the function route_set_nbr_items_per_page when sending a zero or
    negative integer as nbr_items_per_page.

    Parameters:
    - client                The web client used to send the request
    - nbr_items_per_page    The value to try to set as the preferred number of
                            items to display per page for the current user
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    test_request = "/settings/web/nbr_items_per_page/set?nbr_items_per_page={}".format(
        nbr_items_per_page
    )

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400


TODO


def test_settings_set_nbr_items_per_page_success(client, fake_data):
    """
    Test the function route_set_nbr_items_per_page when sending an expected
    value as nbr_items_per_page.

    Parameters:
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    """

    """
    TODO
    # This is to establish a 'current_user'
    current_user_mila_email = fake_data["users"][0]["mila_email_username"]  # No check about the users length is done, because we want an error if the fake_data are not usable
    print(current_user_mila_email)
    response = client.get("/login/testing?user_id={}".format(current_user_mila_email))
    assert response.status_code == 200

    # Get the database
    mc = get_db()

    # Retrieve the preferred number of items to display per page for this user
    D_user = mc["users"].find_one(
        {"mila_email_username": current_user_mila_email}
    )

    # Retrieve its nbr_items_per_page, from its settings
    old_nbr_items_per_page = D_user["web_settings"]["nbr_items_per_page"]

    # Add a 12 (arbitrarily chosen) to this value (this way, we are sure to
    # try to set nbr_items_per_page to a positive number)
    new_nbr_items_per_page = old_nbr_items_per_page + 12

    # Define the request to test
    test_request = "/settings/web/nbr_items_per_page/set?nbr_items_per_page={}".format(new_nbr_items_per_page)

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 200

    # Check if the redirection has correctly be done
    assert response.headers["Location"] == "/settings/"

    # Check if the settings value has correctly been updated
    # Retrieve again the current user from the database
    D_user = mc["users"].find_one(
        {"mila_email_username": current_user_mila_email}
    )

    # Assert that the value of the setting we have update is the expected one
    assert D_user["web_settings"]["nbr_items_per_page"] == new_nbr_items_per_page
    """
    assert True == False


# Check if the dark mode has been set
def test_settings_set_dark_mode():
    assert True == False


# Check if the light mode has been set
def test_settings_unset_dark_mode():
    assert False == True
