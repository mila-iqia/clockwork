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


def test_settings_set_date_format_missing_argument(client):
    """
    Test the function route_set_date_format without sending a
    date_format as argument.

    Parameters:
    - client    The web client used to send the request
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Retrieve the response to the call we are testing
    response = client.get("/settings/web/date_format/set")

    # Check if the response is the expected one
    assert response.status_code == 400


@pytest.mark.parametrize("date_format", ["test", 1.3, True])
def test_settings_set_date_format_wrong_type(client, date_format):
    """
    Test the function route_set_date_format when sending the wrong type
    for date_format.

    Parameters:
    - client                The web client used to send the request
    - date_format           The value to try to set as the preferred date
                            format used to display the "date part" of the
                            timestamps for the current user
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    test_request = "/settings/web/date_format/set?date_format={}".format(date_format)

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400


def test_settings_set_time_format_missing_argument(client):
    """
    Test the function route_set_time_format without sending a
    time_format as argument.

    Parameters:
    - client    The web client used to send the request
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Retrieve the response to the call we are testing
    response = client.get("/settings/web/time_format/set")

    # Check if the response is the expected one
    assert response.status_code == 400


@pytest.mark.parametrize("time_format", ["notanexpectedtimeformat", 34.789, False])
def test_settings_set_time_format_wrong_type(client, time_format):
    """
    Test the function route_set_time_format when sending the wrong type
    for time_format.

    Parameters:
    - client                The web client used to send the request
    - time_format           The value to try to set as the preferred time
                            format used to display the "time part" of the
                            timestamps for the current user
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    test_request = "/settings/web/time_format/set?time_format={}".format(time_format)

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400
