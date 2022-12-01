from flask import session
from flask_login import current_user
from flask_login import FlaskLoginClient
import pytest

from clockwork_web.db import get_db
from clockwork_web.user import User


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
    test_request = (
        f"/settings/web/nbr_items_per_page/set?nbr_items_per_page={nbr_items_per_page}"
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
    test_request = (
        f"/settings/web/nbr_items_per_page/set?nbr_items_per_page={nbr_items_per_page}"
    )

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400


@pytest.mark.parametrize(
    "page_name,column_name",
    [
        (
            "not_an_expected_page",
            "job_id",
        ),  # Unexpected page, "correct" column (as long as we consider this correct, as an undefined page implies no associated expected column)
        ("dashboard", "not_an_expected_column"),  # Correct page, unexpected column
        (
            None,
            "job_id",
        ),  # No page, "correct" column (as long as we consider this correct, as no page implies no associated expected column)
        ("jobs_list", None),  # Correct column, no page
        (None, None),  # No page and no column
    ],
)
def test_settings_set_column_display_bad_request(
    client, fake_data, page_name, column_name
):
    """
    Test the function route_set_column_display when sending incomplete or unexpected arguments
    and assert the result is 400 (Bad Request).

    Parameters:
    - client
    - page_name
    - column_name
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    if page_name == None and column_name == None:
        test_request = "/settings/web/column/set"
    elif page_name == None:
        test_request = f"/settings/web/column/set?column={column_name}"
    elif column_name == None:
        test_request = f"/settings/web/column/set?page={page_name}"
    else:
        test_request = f"/settings/web/column/set?page={page_name}&column={column_name}"

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400
