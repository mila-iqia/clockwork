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
    assert response.status_code == 400 # Bad Request

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
    assert response.status_code == 400 # Bad Request

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
    assert response.status_code == 400 # Bad Request

@pytest.mark.parametrize("date_format", ["words", "unix_timestamp", "MM/DD/YYYY"])
def test_settings_set_date_format_success(client, fake_data, date_format):
    """
    Test the function route_set_date_format when the operation is
    done successfully.

    Parameters:
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    - date_format   The format to display the dates to store in the user's settings
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0
    # Define the user used to test the function
    user_id = fake_data["users"][0]["mila_email_username"]

    # Log in to Clockwork in order to have an active current user
    login_response = client.get(f"/login/testing?user_id={user_id}")
    assert login_response.status_code == 302  # Redirect

    # Define the request to test
    test_request = f"/settings/web/date_format/set?date_format={date_format}"
    # Retrieve the response to the call we are testing
    response = client.get(test_request)
    # Check if the response is the expected one
    assert response.status_code == 302 # Redirect

    # Retrieve the user data
    D_user = get_db()["users"].find_one({"mila_email_username": user_id})
    # Assert the date format setting has been modified
    assert D_user["web_settings"]["date_format"] == date_format

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302 # Redirect

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
    assert response.status_code == 400 # Bad Request


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
    assert response.status_code == 400 # Bad Request


@pytest.mark.parametrize("time_format", ["24h", "AM/PM"])
def test_settings_set_time_format_success(client, fake_data, time_format):
    """
    Test the function route_set_time_format when the operation is
    done successfully.

    Parameters:
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    - time_format   The value to try to set as the preferred time
                    format used to display the "time part" of the
                    timestamps for the current user
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0
    # Define the user used to test the function
    user_id = fake_data["users"][0]["mila_email_username"]

    # Log in to Clockwork in order to have an active current user
    login_response = client.get(f"/login/testing?user_id={user_id}")
    assert login_response.status_code == 302  # Redirect

    # Define the request to test
    test_request = f"/settings/web/time_format/set?time_format={time_format}"
    # Retrieve the response to the call we are testing
    response = client.get(test_request)
    # Check if the response is the expected one
    assert response.status_code == 302 # Redirect

    # Retrieve the user data
    D_user = get_db()["users"].find_one({"mila_email_username": user_id})
    # Assert the time format setting has been modified
    assert D_user["web_settings"]["time_format"] == time_format

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302 # Redirect


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
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    - page_name     The page name on which the provided job property should appear or not regarding the web setting value
    - column_name   The job property we try to change whether or not it is displayed
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
    assert response.status_code == 400 # Bad Request

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
def test_settings_unset_column_display_bad_request(
    client, fake_data, page_name, column_name
):
    """
    Test the function route_unset_column_display when sending incomplete or unexpected arguments
    and assert the result is 400 (Bad Request).

    Parameters:
    - client        The web client used to send the request
    - fake_data     The data on which our tests are based
    - page_name     The page name on which the provided job property should appear or not regarding the web setting value
    - column_name   The job property we try to change whether or not it is displayed
    """
    # This is to establish a 'current_user'
    client.get("/settings/")

    # Define the request to test
    if page_name == None and column_name == None:
        test_request = "/settings/web/column/unset"
    elif page_name == None:
        test_request = f"/settings/web/column/unset?column={column_name}"
    elif column_name == None:
        test_request = f"/settings/web/column/unset?page={page_name}"
    else:
        test_request = (
            f"/settings/web/column/unset?page={page_name}&column={column_name}"
        )

    # Retrieve the response to the call we are testing
    response = client.get(test_request)

    # Check if the response is the expected one
    assert response.status_code == 400 # Bad Request


@pytest.mark.parametrize(
    "page_name,column_name",
    [("jobs_list", "job_id")],
)
def test_settings_set_and_unset_column_display_good_request(
    client, fake_data, page_name, column_name
):
    """
    Test the functions route_set_column_display and route_unset_column_display when the
    corresponding updates are done

    Parameters:
    - client        The web client used to send the requests
    - fake_data     The data on which our tests are based
    - page_name     The page name on which the provided job property should appear or not regarding the web setting value
    - column_name   The job property we try to change whether or not it is displayed
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0
    # Define the user used to test the function
    user_id = fake_data["users"][0]["mila_email_username"]

    # Log in to Clockwork in order to have an active current user
    login_response = client.get(f"/login/testing?user_id={user_id}")
    assert login_response.status_code == 302  # Redirect

    # Check the current value of the web setting we want to update through
    # our requests
    try:
        previous_value = fake_data["users"][0]["web_settings"][page_name][column_name]
    except Exception:
        previous_value = True  # Default value if the setting has not been defined. Anyway, set and unset are tested below

    # Realize the operation twice, in order to set the column display setting to True and False (or reverse,
    # regarding of its first value)
    for i in range(0, 2):
        # Define the request to test
        if not previous_value:  # If the web setting value is False, set it to True
            test_request = (
                f"/settings/web/column/set?page={page_name}&column={column_name}"
            )
        else:  # If the web setting value is True, set it to False
            test_request = (
                f"/settings/web/column/unset?page={page_name}&column={column_name}"
            )
        # Retrieve the response to the call we are testing
        response = client.get(test_request)
        # Check if the response is the expected one
        assert response.status_code == 200 # Success

        # Retrieve the user data
        D_users = get_db()["users"].find_one({"mila_email_username": user_id})
        # Assert the column display value has been modified
        assert D_users["web_settings"]["column_display"][page_name][column_name] == (
            not previous_value
        )

        previous_value = not previous_value

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302 # Redirect
