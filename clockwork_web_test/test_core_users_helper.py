"""
Tests for the clockwork_web.core.users_helper functions.
"""

import pytest

from clockwork_web.core.users_helper import *
from clockwork_web.core.users_helper import _set_web_setting
from clockwork_web.db import init_db, get_db


@pytest.mark.parametrize(
    "setting_name",
    ["unexpectedsetting", -1, 4.5, False, {}, ["blbl"]],
)
def test_get_default_setting_value_wrong_setting_name(setting_name):
    """
    Test the function get_default_setting_value when an unexpected setting_name
    is provided

    Parameters:
        setting_name    The name of the unexpected setting_name to check
    """
    assert get_default_setting_value(setting_name) == None


def test_get_default_setting_value_nbr_items_per_page():
    """
    Test the function get_default_setting_value when setting_name is "nbr_items_per_page".
    """
    assert get_default_setting_value("nbr_items_per_page") == 25


def test_get_default_setting_value_dark_mode():
    """
    Test the function get_default_setting_value when setting_name is "dark_mode".
    """
    assert get_default_setting_value("dark_mode") == False


def test_set_web_setting_with_unknown_user(app, fake_data):
    """
    Test the function _set_web_setting with an unknown user.

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Set the dark mode for a user who does not exist to True and get the status code
        # of the operation (in this case, we have valid setting_key and setting_value)
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = _set_web_setting(
            unknown_mila_email_username, "dark_mode", True
        )

        # Check the status code
        assert status_code == 500

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_set_web_setting_with_wrong_setting_key(app, fake_data):
    """
    Test the function _set_web_setting with a known user, but an unexsting
    setting_key

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Set an unexpected setting by using _set_web_setting and get the status code of the operation
        unexpected_setting = "settingdoesnotexist"
        (status_code, _) = _set_web_setting(
            known_mila_email_username, unexpected_setting, 42
        )

        # Check the status code
        assert status_code == 400

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [("nbr_items_per_page", True), ("dark_mode", 6)],
)
def test_set_web_setting_incorrect_value_for_existing_setting(
    app, fake_data, setting_key, setting_value
):
    """
    Test the function _set_web_setting with a known user, but an incorrect value
    type for the setting nbr_items_per_page

    Parameters:
    - app               The scope of our tests, used to set the context
                        (to access MongoDB)
    - fake_data         The data on which our tests are based
    - setting_key       The key identifying the setting we want to update
    - setting_value     The value to try to set for the setting. For the purpose
                        of the test, its type must not correspond to the expected
                        type of the setting
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to set a wrong value type for the setting and get the status code of the operation
        (status_code, _) = _set_web_setting(
            known_mila_email_username, setting_key, setting_value
        )

        # Check the status code
        assert status_code == 400

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "value",
    [54, 22, 0, -6],
)
def test_set_web_setting_set_nbr_items_per_page(app, fake_data, value):
    """
    Test the function _set_web_setting with a known user for the setting
    nbr_items_per_page

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    - value         The value to set
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Retrieve value of the user's nbr_items_per_page setting
        previous_nbr_items_per_page = known_user["web_settings"]["nbr_items_per_page"]

        # Set the setting nbr_items_per_page of the user to value and get the status code of the operation
        (status_code, _) = _set_web_setting(
            known_mila_email_username, "nbr_items_per_page", value
        )

        # Check the status code
        assert status_code == 200

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"]["nbr_items_per_page"] == value
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "nbr_items_per_page":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


def test_set_web_setting_set_dark_mode(app, fake_data):
    """
    Test the function _set_web_setting with a known user. Modify the value for
    the setting dark_mode

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Retrieve value of the user's dark_mode setting
        previous_dark_mode = known_user["web_settings"]["dark_mode"]

        # Set the setting dark_mode of the user to True if its previous value
        # was False, and to False if its previous value was True
        new_dark_mode = not previous_dark_mode
        # ... set this new value and get the status code of the operation
        (status_code, _) = _set_web_setting(
            known_mila_email_username, "dark_mode", new_dark_mode
        )

        # Check the status code
        assert status_code == 200

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of dark_mode with the new value we tried to set
        assert D_user["web_settings"]["dark_mode"] == new_dark_mode
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "dark_mode":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [
        ("settingdoesnotexist", 3),
        ("column_display.dashboard.not_a_column", True),
        ("column_display.not_a_page.job_id", False),
    ],
)
def test_is_correct_type_for_web_setting_with_unexpected_web_setting(
    setting_key, setting_value
):
    """
    Test the function is_correct_type_for_web_setting when an unexpected
    setting_key is provided

    Parameters:
    - setting_key       The key identifying the setting we want to update
    - setting_value     The value to try to set for the setting. For the purpose
                        of the test, its type must not correspond to the expected
                        type of the setting
    """
    assert is_correct_type_for_web_setting(setting_key, setting_value) == False


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [
        ("nbr_items_per_page", 7.89),
        ("nbr_items_per_page", True),
        ("dark_mode", "test"),
        ("dark_mode", 52.90),
        ("date_format", 45),
        ("date_format", True),
        ("date_format", "notacorrectdateformat"),
        ("time_format", 4986.57),
        ("time_format", False),
        ("time_format", "notacorrecttimeformat"),
        ("column_display.dashboard.job_id", 45),
        ("column_display.dashboard.job_id", "not a string expected"),
    ],
)
def test_is_correct_type_for_web_setting_with_incorrect_value_type(
    setting_key, setting_value
):
    """
    Test the function is_correct_type_for_web_setting with an existing setting
    key, but an unexpected type for the value to set

    Parameters:
    - setting_key       The key identifying the setting we want to update
    - setting_value     The value to try to set for the setting. For the purpose
                        of the test, its type must not correspond to the expected
                        type of the setting
    """
    assert is_correct_type_for_web_setting(setting_key, setting_value) == False


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [
        ("nbr_items_per_page", 10),
        ("nbr_items_per_page", 567),
        ("dark_mode", False),
        ("dark_mode", True),
        ("date_format", "words"),
        ("date_format", "YYYY/MM/DD"),
        ("time_format", "24h"),
        ("time_format", "AM/PM"),
        ("column_display.dashboard.job_id", True),
        ("column_display.dashboard.job_id", False),
    ],
)
def test_is_correct_type_for_web_setting_success(setting_key, setting_value):
    """
    Test the function is_correct_type_for_web_setting with an existing setting
    key, and a value to set presenting the expected type

    Parameters:
    - setting_key       The key identifying the setting we want to update
    - setting_value     The value to try to set for the setting. For the purpose
                        of the test, its type must correspond to the expected
                        type of the setting
    """
    assert is_correct_type_for_web_setting(setting_key, setting_value) == True


def test_set_items_per_page_with_unknown_user(app, fake_data):
    """
    Test the function set_items_per_page with an unknown user.

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Set the dark mode for a user who does not exist to True and get the status code of the operation
        # (in this case, we have valid setting_key and setting_value)
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = set_items_per_page(unknown_mila_email_username, 5)

        # Check the status code
        assert status_code == 500

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "value",
    [0, -1, -36],
)
def test_set_items_per_page_set_negative_number(app, fake_data, value):
    """
    Test the function set_items_per_page with a known user, and a negative value
    (or 0) for the setting nbr_items_per_page

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    - value         The value to set. It must be negative or 0 for the purpose
                    of the test
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Set the setting nbr_items_per_page of the user to a negative number
        # (or 0) and get the status code of the operation
        (status_code, _) = set_items_per_page(known_mila_email_username, value)

        # Check the status code
        assert status_code == 200

        # Assert that the default value of the nbr_items_per_page setting
        # has been set for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of nbr_items_per_page with the default value of
        # the setting nbr_items_per_page
        assert D_user["web_settings"][
            "nbr_items_per_page"
        ] == get_default_setting_value("nbr_items_per_page")
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "nbr_items_per_page":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


@pytest.mark.parametrize(
    "value",
    [True, "blabla", 5.67],
)
def test_set_items_per_page_with_incorrect_value_type(app, fake_data, value):
    """
    Test the function set_items_per_page with a known user, but an incorrect value
    type for the setting nbr_items_per_page

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - value         The value to set. For the purpose of the test, must present
                    an incorrect type
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to set a wrong value type for the setting and get the status code of the operation
        (status_code, _) = set_items_per_page(known_mila_email_username, value)

        # Check the status code
        assert status_code == 400

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "value",
    [54, 23],
)
def test_set_items_per_page_set_positive_number(app, fake_data, value):
    """
    Test the function set_items_per_page with a known user, and a positive
    integer as value (which is an expected value)

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - value         A positive number, which is used to update the number
                    of items to display per page for a specific user
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Set the setting nbr_items_per_page of the user to a positive number and get the status code of the operation
        (status_code, _) = set_items_per_page(known_mila_email_username, value)

        # Check the status code
        assert status_code == 200

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"]["nbr_items_per_page"] == value
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "nbr_items_per_page":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


def test_reset_items_per_page_with_unknown_user(app, fake_data):
    """
    Test the function reset_items_per_page with an unknown user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Try to reset the preferred number of items per page to the default
        # value for a user who does not exist and get the status code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = reset_items_per_page(unknown_mila_email_username)

        # Check the status code
        assert status_code == 500

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_reset_items_per_page_with_known_user(app, fake_data):
    """
    Test the function reset_items_per_page with a known user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # First set its nbr_items_per_page to a number different from the
        # default number and get the status code of the operation
        (status_code, _) = set_items_per_page(known_user["mila_email_username"], 56)

        # Check the status code
        assert status_code == 200

        # Then reset this value and get the status code of the operation
        (status_code, _) = reset_items_per_page(known_user["mila_email_username"])

        # Check the status code
        assert status_code == 200

        # Assert that the default value has been set for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"][
            "nbr_items_per_page"
        ] == get_default_setting_value(
            "nbr_items_per_page"
        )  # TODO: maybe put it in the configuration file?
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "nbr_items_per_page":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


def test_enable_dark_mode_with_unknown_user(app, fake_data):
    """
    Test the function enable_dark_mode with an unknown user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Try to enable the dark mode for a user who does not exist and get the status code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = enable_dark_mode(unknown_mila_email_username)

        # Check the status code
        assert status_code == 500

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_enable_dark_mode_success(app, fake_data):
    """
    Test the function enable_dark_mode with a known user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # First set its dark mode option to False and get the status code of the operation
        (status_code, _) = _set_web_setting(
            known_user["mila_email_username"], "dark_mode", False
        )

        # Check the status code
        assert status_code == 200

        # TODO: I did not check if the modification has been done because it is
        # suppose to be tested in another function, but we can discuss it

        # Then enable the dark mode for this user and get the status code of the operation
        (status_code, _) = enable_dark_mode(known_user["mila_email_username"])

        # Check the status code
        assert status_code == 200

        # Assert that True has been set to the dark_mode setting for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of dark_mode with True
        assert D_user["web_settings"]["dark_mode"] == True
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "dark_mode":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


def test_disable_dark_mode_with_unknown_user(app, fake_data):
    """
    Test the function disable_dark_mode with an unknown user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Try to disable the dark mode for a user who does not exist and get the status code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = disable_dark_mode(unknown_mila_email_username)

        # Check the status code
        assert status_code == 500

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_disable_dark_mode_success(app, fake_data):
    """
    Test the function disable_dark_mode with a known user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # First set its dark mode option to True and get the status code of the operation
        (status_code, _) = _set_web_setting(
            known_user["mila_email_username"], "dark_mode", True
        )

        # Check the status code
        assert status_code == 200

        # TODO: I did not check if the modification has been done because it is
        # suppose to be tested in another function, but we can discuss it

        # Then disable the dark mode for this user and get the status code of the operation
        (status_code, _) = disable_dark_mode(known_user["mila_email_username"])

        # Check the status code
        assert status_code == 200

        # Assert that False has been set to the dark_mode setting for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of dark_mode with False
        assert D_user["web_settings"]["dark_mode"] == False
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "dark_mode":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


@pytest.mark.parametrize(
    "incorrect_date_format",
    [54, "not_a_correct_date_format", True, 3.4, ["unix_timestamp"]],
)
def test_set_date_format_with_incorrect_value_type(
    app, fake_data, incorrect_date_format
):
    """
    Test the function set_date_format while providing incorrect parameters

    Parameters:
    - app                       The scope of our tests, used to set the context
                                (to access MongoDB)
    - fake_data                 The data on which our tests are based
    - incorrect_date_format     An element which does not correspond to what is expected
                                from a date format
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to update the preferred date format of the user with a value
        # of an unexpected type
        (status_code, _) = set_date_format(
            known_mila_email_username, incorrect_date_format
        )

        # Check the status code
        assert status_code == 400  # Bad Request

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_set_date_format_with_unknown_user(app, fake_data):
    """
    Test the function set_date_format while providing a user who does
    not exist

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Try to update a date format for a user who does not exist and get the status
        # code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"  # Inexistent user
        date_format = "unix_timestamp"  # Valid date format
        (status_code, _) = set_date_format(unknown_mila_email_username, date_format)

        # Check the status code
        assert status_code == 500  # Internal Server Error

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "valid_date_format",
    ["DD/MM/YYYY", "unix_timestamp"],
)
def test_set_date_format_success(app, fake_data, valid_date_format):
    """
    Test the function set_date_format

    Parameters:
    - app                   The scope of our tests, used to set the context
                            (to access MongoDB)
    - fake_data             The data on which our tests are based
    - valid_date_format     An element which does not correspond to what is expected
                            from a date format
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to update the preferred date format of the user with a value
        # of an expected type
        (status_code, _) = set_date_format(known_mila_email_username, valid_date_format)

        # Check the status code
        assert status_code == 200  # Success

        # Assert that the value has correctly been updated
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )

        # Compare the value of the date format with the expected one
        assert D_user["web_settings"]["date_format"] == valid_date_format
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "date_format":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


@pytest.mark.parametrize(
    "incorrect_time_format",
    [237000, "not_a_correct_time_format", False, 789.09, ["AM/PM"]],
)
def test_set_time_format_with_incorrect_value_type(
    app, fake_data, incorrect_time_format
):
    """
    Test the function set_time_format while providing incorrect parameters

    Parameters:
    - app                       The scope of our tests, used to set the context
                                (to access MongoDB)
    - fake_data                 The data on which our tests are based
    - incorrect_time_format     An element which does not correspond to what is expected
                                from a time format
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to update the preferred time format of the user with a value
        # of an unexpected type
        (status_code, _) = set_time_format(
            known_mila_email_username, incorrect_time_format
        )

        # Check the status code
        assert status_code == 400  # Bad Request

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_set_time_format_with_unknown_user(app, fake_data):
    """
    Test the function set_time_format while providing a user who does not exist

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Try to update a time format for a user who does not exist and get the status
        # code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"  # Inexistent user
        time_format = "24h"  # Valid time format
        (status_code, _) = set_time_format(unknown_mila_email_username, time_format)

        # Check the status code
        assert status_code == 500  # Internal Server Error

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "valid_time_format",
    ["AM/PM", "24h"],
)
def test_set_time_format_success(app, fake_data, valid_time_format):
    """
    Test the function set_time_format

    Parameters:
    - app                   The scope of our tests, used to set the context
                            (to access MongoDB)
    - fake_data             The data on which our tests are based
    - valid_time_format     An element which does not correspond to what is expected
                            from a time format
    """
    # Assert that the users of the fake data exist and are not empty
    assert "users" in fake_data and len(fake_data["users"]) > 0

    # Get an existing user from the fake_data
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Try to update the preferred time format of the user with a value
        # of an expected type
        (status_code, _) = set_time_format(known_mila_email_username, valid_time_format)

        # Check the status code
        assert status_code == 200  # Success

        # Assert that the value has correctly been updated
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of the time format with the expected one
        assert D_user["web_settings"]["time_format"] == valid_time_format
        # Assert that the other web settings remain unchanged
        for setting_key in known_user["web_settings"].keys():
            if setting_key != "time_format":
                assert (
                    known_user["web_settings"][setting_key]
                    == D_user["web_settings"][setting_key]
                )


@pytest.mark.parametrize("page_name,column_name", [("dashboard", "start_time")])
def test_enable_column_display_with_unknown_user(
    app, fake_data, page_name, column_name
):
    """
    Test the function enable_column_display with an unknown user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Try to enable the display of the given column on the given page for a user who does not exist and
        # get the status code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = enable_column_display(
            unknown_mila_email_username, page_name, column_name
        )

        # Check the status code
        assert status_code == 500  # Internal Server Error

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


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
def test_enable_column_display_bad_request(app, fake_data, page_name, column_name):
    """
    Test the function enable_column_display with unexpected page_name and column_name

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # Then disable the corresponding display setting for this user and get the status code of the operation
        (status_code, _) = enable_column_display(
            known_user["mila_email_username"], page_name, column_name
        )

        # Check the status code
        assert status_code == 400  # Bad Request

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize("page_name,column_name", [("dashboard", "start_time")])
def test_enable_column_display_success(app, fake_data, page_name, column_name):
    """
    Test the function enable_column_display when the operation is successful

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # Then disable the corresponding display setting for this user and get the status code of the operation
        (status_code, _) = enable_column_display(
            known_user["mila_email_username"], page_name, column_name
        )

        # Check the status code
        assert status_code == 200  # Success

        # Assert that the display setting for this column is enabled for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )

        # Compare the value of the column display setting with True
        assert D_user["web_settings"]["column_display"][page_name][column_name] == True


@pytest.mark.parametrize("page_name,column_name", [("dashboard", "start_time")])
def test_disable_column_display_with_unknown_user(
    app, fake_data, page_name, column_name
):
    """
    Test the function disable_column_display with an unknown user

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Try to enable the display of the given column on the given page for a user who does not exist
        # and get the status code of the operation
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        (status_code, _) = disable_column_display(
            unknown_mila_email_username, page_name, column_name
        )

        # Check the status code
        assert status_code == 500  # Internal Server Error

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


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
def test_disable_column_display_bad_request(app, fake_data, page_name, column_name):
    """
    Test the function disable_column_display with unexpected page_name and column_name

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # Then disable the corresponding display setting for this user and get the status code of the operation
        (status_code, _) = disable_column_display(
            known_user["mila_email_username"], page_name, column_name
        )

        # Check the status code
        assert status_code == 400  # Bad Request

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize("page_name,column_name", [("dashboard", "start_time")])
def test_disable_column_display_success(app, fake_data, page_name, column_name):
    """
    Test the function disable_column_display when the operation is successful

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    - page_name     Name of the page on which the job property corresponding to the column should be displayed
    - column_name   Name of the column (corresponding to a job property) whose display is enabled
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get an existing user from the fake_data
        known_user = fake_data["users"][0]

        # Then disable the corresponding display setting for this user and get the status code of the operation
        (status_code, _) = disable_column_display(
            known_user["mila_email_username"], page_name, column_name
        )

        # Check the status code
        assert status_code == 200  # Success

        # Assert that the display setting for this column is enabled for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one(
            {"mila_email_username": known_user["mila_email_username"]}
        )
        # Compare the value of the column display setting with True
        assert D_user["web_settings"]["column_display"][page_name][column_name] == False


def test_get_nbr_items_per_page_none_user(app):
    """
    Test the function get_nbr_items_per_page when the user is None.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    """
    # Use the app context
    with app.app_context():
        # Assert that the returned value is the default value
        assert get_nbr_items_per_page(None) == get_default_setting_value(
            "nbr_items_per_page"
        )


def test_get_nbr_items_per_page_unknown_user(app):
    """
    Test the function get_nbr_items_per_page when the user is not stored in
    the database.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    """
    # Use the app context
    with app.app_context():
        # Assert that the returned value is the default value
        assert get_nbr_items_per_page("unknownuser") == get_default_setting_value(
            "nbr_items_per_page"
        )


def test_get_nbr_items_per_page_known_user(app, fake_data):
    """
    Test the function get_nbr_items_per_page when the user is stored in
    the database.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get a user from the fake_data
        D_known_user = fake_data["users"][0]

        # Retrieve its nbr_items_per_page through the function we are testing
        retrieved_nbr_items_per_page = get_nbr_items_per_page(
            D_known_user["mila_email_username"]
        )

        # Compare its nbr_items_per_page with the one we know
        assert (
            retrieved_nbr_items_per_page
            == D_known_user["web_settings"]["nbr_items_per_page"]
        )

        # (The following is to be sure that we don't always return the default value)
        # Set a new value to its nbr_items_per_page and get the status code of the operation
        new_value = (
            retrieved_nbr_items_per_page + 33
        )  # Thus, we are sure that the values differ
        (status_code, _) = set_items_per_page(
            D_known_user["mila_email_username"], new_value
        )

        # Check the status code
        assert status_code == 200

        # Retrieve its nbr_items_per_page through the function we are testing
        retrieved_nbr_items_per_page = get_nbr_items_per_page(
            D_known_user["mila_email_username"]
        )

        # Compare its nbr_items_per_page with the one we know
        assert retrieved_nbr_items_per_page == new_value


def test_get_users_one_none_user(app):
    """
    Test the function get_users_one when the user is None.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    """
    # Use the app context
    with app.app_context():
        # Assert that the returned value is None
        assert get_users_one(None) == None


def test_get_users_one_unknown_user(app):
    """
    Test the function get_users_one when the user is not stored in
    the database.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    """
    # Use the app context
    with app.app_context():
        # Assert that the returned value is None
        assert get_users_one("unknownuser") == None


def test_get_users_one_known_user(app, fake_data):
    """
    Test the function get_users_one when the user is stored in
    the database.

    Parameters:
    - app           The scope of our tests, used to set the context
                    (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Assert that the users of the fake data exist and are not empty
        assert "users" in fake_data and len(fake_data["users"]) > 0

        # Get a user from the fake_data
        D_known_user = fake_data["users"][0]

        # Retrieve it through the function we are testing
        D_retrieved_user = get_users_one(D_known_user["mila_email_username"])

        # Compare it with the one we know
        assert D_retrieved_user == D_known_user


@pytest.mark.parametrize(
    "user_dict,expected_clusters",
    [
        # User with a Mila account and a CC account
        (
            # - user dictionary
            {
                "mila_email_username": "student1@mila.quebec",
                "status": "enabled",
                "clockwork_api_key": "000aaa01",
                "mila_cluster_username": "milauser1",
                "cc_account_username": "ccuser1",
                "cc_account_update_key": None,
                "web_settings": {"nbr_items_per_page": 40, "dark_mode": False},
            },
            # - expected clusters
            ["mila", "beluga", "cedar", "graham", "narval"],
        ),
        # User with only a Mila account
        (
            # - user dictionary
            {
                "mila_email_username": "student1@mila.quebec",
                "status": "enabled",
                "clockwork_api_key": "000aaa01",
                "mila_cluster_username": "milauser1",
                "cc_account_username": None,
                "cc_account_update_key": None,
                "web_settings": {"nbr_items_per_page": 40, "dark_mode": False},
            },
            # - expected clusters
            ["mila"],
        ),
        # User with only a CC account (this should not happen - for now
        # at least -, but just in case)
        (
            # - user dictionary
            {
                "mila_email_username": "student1@mila.quebec",
                "status": "enabled",
                "clockwork_api_key": "000aaa01",
                "mila_cluster_username": None,
                "cc_account_username": "ccuser1",
                "cc_account_update_key": None,
                "web_settings": {"nbr_items_per_page": 40, "dark_mode": False},
            },
            # - expected clusters
            ["beluga", "cedar", "graham", "narval"],
        ),
    ],
)
def test_get_available_clusters_from_user_dict(user_dict, expected_clusters):
    """
    Test the function get_available_clusters_from_user_dict.

    Parameters:
    - user_dict             Dictionary of the user for who we want to get
                            the available clusters
    - expected_clusters     Array of Strings containing the name of the clusters
                            we expect the function to retrieve
    """
    # Retrieve the available clusters for the user from the user dict
    # by calling the function we want to test
    retrieved_clusters = get_available_clusters_from_user_dict(user_dict)

    # Check if the retrieved clusters are the expected ones
    assert set(expected_clusters) == set(retrieved_clusters)


@pytest.mark.parametrize(
    "user_id,expected_clusters",
    [
        ("student00@mila.quebec", ["mila", "beluga", "cedar", "graham", "narval"]),
        (
            "student06@mila.quebec",
            ["mila"],
        ),  # student06 is the one in the fake data who does not have a DRAC account
    ],
)
def test_get_available_clusters_from_db(app, user_id, expected_clusters):
    """
    Test the function get_available_clusters_from_db.

    Parameters:
    - app                   The scope of our tests, used to set the context
                            (to access MongoDB)
    - user_id               The ID of the user for who we want to get the available
                            clusters
    - expected_clusters     Array of Strings containing the name of the clusters
                            we expect the function to retrieve
    """
    # Use the app context
    with app.app_context():
        # Retrieve the available clusters for the user from db
        # by calling the function we want to test
        retrieved_clusters = get_available_clusters_from_db(user_id)

        # Check if the retrieved clusters are the expected ones
        assert set(expected_clusters) == set(retrieved_clusters)


# Helpers
def assert_no_user_has_been_modified(fake_data):
    """
    Assert that the users list retrieved from the database is the same that the
    users list stored in the fake_data.

    Parameters:
    - fake_data     The data on which our tests are based
    """
    # Retrieve the users list from the database
    mc = get_db()
    LD_users = list(mc["users"].find({}, {"_id": 0}))
    # Compare it to the fake data content
    assert fake_data["users"] == LD_users
