"""
Tests for the clockwork_web.core.users_helper functions.
"""

import pytest

from clockwork_web.core.users_helper import *
from clockwork_web.db import init_db, get_db


def test_set_web_setting_with_unknown_user(app, fake_data):
    """
    Test the function set_web_setting with an unknown user.

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Use the app context
    with app.app_context():
        # Set the dark mode for unexisting user to True
        # (in this case, we have valid setting_key and setting_value)
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        set_web_setting(unknown_mila_email_username, "dark_mode", True)

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


def test_set_web_setting_with_wrong_setting_key(app, fake_data):
    """
    Test the function set_web_setting with a known user, but an unexsting
    setting_key

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"] # No check about the users length is done, because we want an error if the fake_data are not usable

    # Use the app context
    with app.app_context():
        # Set an unexisting setting by using set_web_setting
        unexisting_setting = "settingdoesnotexist"
        set_web_setting(known_mila_email_username, unexisting_setting, 42)

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [("nbr_items_per_page", True),
    ("dark_mode", 6)],
)
def test_set_web_setting_incorrect_value_for_existing_setting(app, fake_data, setting_key, setting_value):
    """
    Test the function set_web_setting with a known user, but an incorrect value
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
    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"] # No check about the users length is done, because we want an error if the fake_data are not usable

    # Use the app context
    with app.app_context():
        # Try to set a wrong value type for the setting
        set_web_setting(known_mila_email_username, setting_key, setting_value)

        # Assert that the users data remains unchanged
        assert_no_user_has_been_modified(fake_data)


@pytest.mark.parametrize(
    "value",
    [54, 22, 0, -6],
)
def test_set_web_setting_set_nbr_items_per_page(app, fake_data, value):
    """
    Test the function set_web_setting with a known user for the setting
    nbr_items_per_page

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    - value         The value to set
    """
    # Get an existing user from the fake_data
    # NB: we don't check about the users length, because we want an error
    # if the fake_data are not usable
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Retrieve value of the user's nbr_items_per_page setting
        previous_nbr_items_per_page = known_user["web_settings"]["nbr_items_per_page"]

        # Set the setting nbr_items_per_page of the user to value
        set_web_setting(known_mila_email_username, "nbr_items_per_page", value)

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"]["nbr_items_per_page"] == value


def test_set_web_setting_set_dark_mode(app, fake_data):
    """
    Test the function set_web_setting with a known user. Modify the value for
    the setting dark_mode

    Parameters:
    - app           The scope of our tests, used to set the context (to access MongoDB)
    - fake_data     The data on which our tests are based
    """
    # Get an existing user from the fake_data
    # NB: we don't check about the users length, because we want an error
    # if the fake_data are not usable
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Retrieve value of the user's dark_mode setting
        previous_dark_mode = known_user["web_settings"]["dark_mode"]

        # Set the setting dark_mode of the user to True if its previous value
        # was False, and to False if its previous value was True
        new_dark_mode = not previous_dark_mode
        # ... and set this new value
        set_web_setting(known_mila_email_username, "dark_mode", new_dark_mode)

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of dark_mode with the new value we tried to set
        assert D_user["web_settings"]["dark_mode"] == new_dark_mode


def test_is_correct_type_for_web_setting_with_unexisting_web_setting():
    """
    Test the function is_correct_type_for_web_setting when an unexisting
    setting_key is provided
    """
    assert is_correct_type_for_web_setting("settingdoesnotexist", 3) == False


@pytest.mark.parametrize(
    "setting_key,setting_value",
    [("nbr_items_per_page", 7.89),
    ("nbr_items_per_page", True),
    ("dark_mode", "test"),
    ("dark_mode", 52.90)],
)
def test_is_correct_type_for_web_setting_with_incorrect_value_type(setting_key, setting_value):
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
    [("nbr_items_per_page", 10),
    ("nbr_items_per_page", 567),
    ("dark_mode", False),
    ("dark_mode", True)],
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
        # Set the dark mode for unexisting user to True
        # (in this case, we have valid setting_key and setting_value)
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        set_items_per_page(unknown_mila_email_username, 5)

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
    # TODO: do we let this check in set_items_per_page or do we move it to
    # set_web_setting?
    # Get an existing user from the fake_data
    # NB: we don't check about the users length, because we want an error
    # if the fake_data are not usable
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Set the setting nbr_items_per_page of the user to a negative number
        # (or 0)
        set_items_per_page(known_mila_email_username, -2)

        # Assert that the default value of the nbr_items_per_page setting
        # has been set for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of nbr_items_per_page with the default value of
        # the setting nbr_items_per_page
        assert D_user["web_settings"]["nbr_items_per_page"] == 40 # TODO: maybe put it in the configuration file?


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
    # Get an existing mila_email_username from the fake_data
    known_mila_email_username = fake_data["users"][0]["mila_email_username"] # No check about the users length is done, because we want an error if the fake_data are not usable

    # Use the app context
    with app.app_context():
        # Try to set a wrong value type for the setting
        set_items_per_page(known_mila_email_username, value)

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
    """
    # Get an existing user from the fake_data
    # NB: we don't check about the users length, because we want an error
    # if the fake_data are not usable
    known_user = fake_data["users"][0]
    known_mila_email_username = known_user["mila_email_username"]

    # Use the app context
    with app.app_context():
        # Set the setting nbr_items_per_page of the user to a positive number
        set_items_per_page(known_mila_email_username, value)

        # Assert that the user has been correctly modified
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"]["nbr_items_per_page"] == value


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
        # value for an unexisting user
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        reset_items_per_page(unknown_mila_email_username)

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
        # Get an existing user from the fake_data
        # NB: we don't check about the users length, because we want an error
        # if the fake_data are not usable
        known_user = fake_data["users"][0]

        # First set its nbr_items_per_page to a number different from the
        # default number
        set_items_per_page(known_user, 56)

        # TODO: I did not check if the modification has been done because it is
        # suppose to be tested in another function, but we can discuss it

        # Then reset this value
        reset_items_per_page(known_user["mila_email_username"])

        # Assert that the default value has been set for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of nbr_items_per_page with the new value we tried to set
        assert D_user["web_settings"]["nbr_items_per_page"] == 40 # TODO: maybe put it in the configuration file?


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
        # Try to enable the dark mode for an unexisting user
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        enable_dark_mode(unknown_mila_email_username)

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
        # Get an existing user from the fake_data
        # NB: we don't check about the users length, because we want an error
        # if the fake_data are not usable
        known_user = fake_data["users"][0]

        # First set its dark mode option to False
        set_web_setting(known_user, "dark_mode", False)

        # TODO: I did not check if the modification has been done because it is
        # suppose to be tested in another function, but we can discuss it

        # Then enable the dark mode for this user
        enable_dark_mode(known_user["mila_email_username"])

        # Assert that True has been set to the dark_mode setting for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of dark_mode with True
        assert D_user["web_settings"]["dark_mode"] == True


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
        # Try to disable the dark mode for an unexisting user
        unknown_mila_email_username = "userdoesntexist@mila.quebec"
        disable_dark_mode(unknown_mila_email_username)

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
        # Get an existing user from the fake_data
        # NB: we don't check about the users length, because we want an error
        # if the fake_data are not usable
        known_user = fake_data["users"][0]

        # First set its dark mode option to True
        set_web_setting(known_user, "dark_mode", True)

        # TODO: I did not check if the modification has been done because it is
        # suppose to be tested in another function, but we can discuss it

        # Then disable the dark mode for this user
        disable_dark_mode(known_user["mila_email_username"])

        # Assert that False has been set to the dark_mode setting for this user
        # Retrieve the user from the database
        mc = get_db()
        # NB: the argument of find_one is the filter to apply to the user list
        # the returned user matches this condition
        D_user = mc["users"].find_one({"mila_email_username": known_user["mila_email_username"]})
        # Compare the value of dark_mode with False
        assert D_user["web_settings"]["dark_mode"] == False


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
    LD_users = list(mc["users"].find({},{"_id": 0}))
    # Compare it to the fake data content
    assert fake_data["users"] == LD_users
