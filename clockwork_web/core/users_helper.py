"""
Helper functions related to the User entity and the users entries from the databas.
"""

from flask_login import current_user
from flask import render_template
import json

from clockwork_web.db import get_db

# Import the functions from clockwork_web.config
from clockwork_web.config import (
    get_config,
    register_config,
    boolean as valid_boolean,
    string as valid_string,
)
from clockwork_web.core.clusters_helper import get_all_clusters

from clockwork_web.core.utils import (
    get_available_date_formats,
    get_available_time_formats,
)

# Load the web settings from the configuration file
register_config("settings.default_values.nbr_items_per_page", validator=int)
register_config("settings.default_values.dark_mode", validator=valid_boolean)
register_config("settings.default_values.language", validator=valid_string)


def get_default_web_settings_values():
    """
    Get a dictionary associating each user web setting to its default value.

    Returns:
        A dictionary associating each user web setting to its default value.
    """
    return get_config("settings.default_values").copy()


def get_web_settings_types():
    """
    Get a dictionary referencing the expected type for each web setting entity

    Returns:
        A dictionary associating each web setting to its expected type.
    """
    return {"nbr_items_per_page": int, "dark_mode": bool, "language": str}


def get_default_setting_value(setting_name):
    """
    Retrieve the default value of one user web setting, identified by its
    setting name

    Parameters:
        setting_name    Name of the settings of which we want to get the
                        default value. For now, it could be "nbr_items_per_page"
                        or "dark_mode"

    Returns:
        The default value for the requested web setting
    """
    if isinstance(setting_name, str):
        return get_default_web_settings_values().get(setting_name, None)
    else:
        return None


def _set_web_setting(mila_email_username, setting_key, setting_value):
    """
    Update an element of a User's web settings. The "web settings" of a
    User are preferences used in the web interface. They are stored in
    the user["web_settings"] dictionary. The User whose settings are updated
    is identified by the "mila_email_username" element of the dictionary he is
    described by.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
        setting_key             The setting's key, as used in the
                                user["web_settings"] dictionary
        setting_value           The value to associate to the referred entity
                                (identified by the setting_key)

    Returns:
        A tuple containing
        - a HTTP status code (200 or 400)
        - a message describing the state of the operation
    """
    # If the type of setting_value is the expected type for an element related
    # to setting_key
    if is_correct_type_for_web_setting(setting_key, setting_value):
        # Retrieve the users collection from the database
        users_collection = get_db()["users"]

        # Update the information in the user's settings
        # (First, the key is reformatted in order to avoid problem.
        # Thus, for the setting "nbr_items_per_page" for instance, the requests
        # looks like:
        #    {
        #        "mila_email_username": "student00@mila.quebec",
        #        "$set": {"web_settings.nbr_items_per_page": 34}
        #    }
        # This is what the variable "web_settings_key" is about.)
        web_settings_key = "web_settings.{}".format(setting_key)
        update_result = users_collection.update_one(
            {
                "mila_email_username": mila_email_username
            },  # identify the element to update
            {"$set": {web_settings_key: setting_value}},  # update to do
        )

        # (We use matched_count here instead of modified_count in order to not return
        # an error if the old value was just the same as the value we want to set)
        if update_result.matched_count == 1:
            # Return 200 (Success) and a success message if one setting has
            # been modified (because there should be only one user corresponding
            # to mila_email_username, and only one web setting corresponding to
            # the setting key for this user)
            return (200, "The setting has been updated.")
        else:
            # Otherwise, return error 500 (Internal Server Error): we do not
            # really know what happened
            return (500, "An error occurred.")
    else:
        # Return 400 (Bad Request) and an error message
        return (400, "The provided value is not expected for this setting.")


def is_correct_type_for_web_setting(setting_key, setting_value):
    """
    Check if an argument can be associated to a specific web setting in a User
    description.

    Parameters:
        setting_key     The setting's key, as used in the user["web_settings"]
                        dictionary
        setting_value   The value to associate to the referred entity
                        (identified by the setting_key)

    Returns:
        True if the type of setting_value and the expected type for an element
        related to setting_key match. False otherwise.
    """
    # Retrieve the types expected for each web setting
    web_settings_types = get_web_settings_types()

    # If the element has a generic registered expected type
    if setting_key in web_settings_types:
        # The problem here is that isinstance(True,int) returns True
        # Thus, we handle boolean differently than any other type
        if type(setting_value) != bool:
            return isinstance(setting_value, web_settings_types[setting_key])
        else:
            return web_settings_types[setting_key] == bool
    else:
        # Check for the web setting associated to the date format
        if setting_key == "date_format":
            return setting_value in get_available_date_formats()
        # Check for the web setting associated to the time format
        elif setting_key == "time_format":
            return setting_value in get_available_time_formats()
        else:
            # If the provided web setting has no expected type defined
            return False


def set_items_per_page(mila_email_username, nbr_items_per_page):
    """
    Set the number of items to display by default for a specific user in a page
    presenting a list, such as a list of jobs, or a list of nodes.
    If nbr_items_per_page is positive, it will be set as value to the setting
    "nbr_items_per_page" of the user. If not, the default value is set.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
        nbr_items_per_page      New number of items to display, to set

    Returns:
        A tuple containing
        - a HTTP status code (200 or 400)
        - a message describing the state of the operation
    """
    # If the value to set is an integer
    if isinstance(nbr_items_per_page, int):
        # Check if nbr_items_per_page is a positive number.
        if nbr_items_per_page <= 0:
            # If not, set the default value for this parameter
            return reset_items_per_page(mila_email_username)

        else:
            # If it is positive, call _set_web_setting
            return _set_web_setting(
                mila_email_username, "nbr_items_per_page", nbr_items_per_page
            )

    # Return 400 (Bad Request) and an error message
    return (400, "The provided value is not expected for this setting")


def reset_items_per_page(mila_email_username):
    """
    Set the number of items to display by default for a specific user in a page
    presenting a list (such as a list of jobs, or a list of nodes) to the
    default value (arbitrarily defined by Clockwork's team).

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting and retrieve the returned status code and status
    # message
    (status_code, status_message) = _set_web_setting(
        mila_email_username,
        "nbr_items_per_page",
        get_default_setting_value("nbr_items_per_page"),
    )

    if status_code == 200:
        # If the status code is 200 (Success), return it and indicates in the message
        # that the setting's value has been set to default
        return (200, "The setting has been reset to its default value.")
    else:
        # Otherwise, returns what the function _set_web_setting has returned
        return (status_code, status_message)


def get_nbr_items_per_page(mila_email_username):
    """
    Retrieve the number of items to display per page, set in the user's settings.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

    Returns:
        The value of nbr_items_per_page from the user's settings if a user has been
        found; the default value of the number of items to display per page otherwise
    """
    # Retrieve the user from mila_email_username
    user = get_users_one(mila_email_username)

    if not user:
        # If no user has been found, return the default value of the number of items
        # to display per page
        return get_default_setting_value("nbr_items_per_page")
    else:
        # If a user has been found, return the value stored in its settings
        v = user.get("web_settings", {}).get("nbr_items_per_page", None)
        if v is None:
            return get_default_setting_value("nbr_items_per_page")
        else:
            return v


def get_users_one(mila_email_username):
    """
    Retrieve a user from the database, based on its mila_email_username.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
    Returns:
        A dictionary presenting the user if it has been found;
        None otherwise.
    """
    # Retrieve the users collection from the database
    users_collection = get_db()["users"]

    # Try to get the user from this collection
    # (The first argument of find_one is the filter we want to apply in order to selection our user.)
    # (The second argument of find_one indicates that we don't want the "_id" element to be included in the returned dictionary)
    user = users_collection.find_one(
        {"mila_email_username": mila_email_username}, {"_id": 0}
    )

    # Return the user. It is a dictionary presenting the user if one has been
    # found, None otherwise.
    return user


def enable_dark_mode(mila_email_username):
    """
    Enable the dark mode display option for a specific user.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting an return its response
    return _set_web_setting(mila_email_username, "dark_mode", True)


def disable_dark_mode(mila_email_username):
    """
    Disable the dark mode display option for a specific user.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting and return its response
    return _set_web_setting(mila_email_username, "dark_mode", False)


def set_language(mila_email_username, language):
    """
    Set the language to use with a specific user.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

        language                The chosen language to associate to this user

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting and return its response
    return _set_web_setting(mila_email_username, "language", language)


def set_date_format(mila_email_username, date_format):
    """
    Set the format of the "date part" of the datetimes to display to a
    specific user on the web interface.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

        date_format             The chosen date format to display timestamps
                                to this user

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting and return its response
    return _set_web_setting(mila_email_username, "date_format", date_format)


def set_time_format(mila_email_username, time_format):
    """
    Set the format of the "time part" of the datetimes to display to a
    specific user on the web interface.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database

        time_format             The chosen time format to display timestamps
                                to this user

    Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
    """
    # Call _set_web_setting and return its response
    return _set_web_setting(mila_email_username, "time_format", time_format)


def render_template_with_user_settings(template_name_or_list, **context):
    """
    Wraps the Flask function render_template in order to send the user's web
    settings to the rendered HTML page.

    Parameters:
        template_name_or_list   The name of the template to render. If a list is
                                given, the first name to exist will be rendered.
        context                 The variables to make available in the template.

    Returns:
        The template rendered by Flask, and containing the web_settings of the
        current user
    """
    context[
        "web_settings"
    ] = current_user.get_web_settings()  # used for templates (old way)
    # used for the actual `web_settings` variable from "base.html" (prompted by GEN-160)
    context["web_settings_json_str"] = json.dumps(context["web_settings"])

    # Send the clusters infos to the template
    context["clusters"] = get_all_clusters()

    return render_template(template_name_or_list, **context)
