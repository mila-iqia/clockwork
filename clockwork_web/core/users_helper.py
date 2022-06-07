"""
Helper functions related to the User entity.
"""

from clockwork_web.db import get_db

# Dictionary referencing the expected type for each web setting entity
# TODO: do we call it "WEB_SETTINGS_TYPES" or do we keep a lowercase syntax?
web_settings_types = {"nbr_items_per_page": int, "dark_mode": boolean}

# default value for the user setting "nbr_items_per_page"
# TODO: do we call it "DEFAULT_NBR_ITEMS_PER_PAGE" or do we keep a lowercase syntax?
default_nbr_items_per_page = 40


def set_web_setting(mila_email_username, setting_key, setting_value):
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
    """
    # If the type of setting_value is the expected type for an element related
    # to setting_key
    if is_correct_type_for_web_setting(setting_key, setting_value):
        # Retrieve the users collection from the database
        users_collection = get_db()["users"]

        # Update the information in the user's settings
        requested_user = users_collection.update_one(
            {
                "mila_email_username": mila_email_username
            },  # identify the element to update
            {"$set": {"web_settings": {setting_key: setting_value}}},  # update to do
        )
    else:
        # TODO: do we raise an error?
        pass


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
    # If the element has a registered expected type
    if setting_key in web_settings_types:
        return isinstance(setting_value, web_settings_types[setting_key])
    else:
        return False  # TODO: raise an error instead?


def set_items_per_page(mila_email_username, nbr_items_per_page):
    """
    Set the number of items to display by default for a specific user in a page
    presenting a list, such as a list of jobs, or a list of nodes.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
        nbr_items_per_page      New number of items to display, to set
    """
    # Call set_web_setting
    set_web_setting(mila_email_username, "nbr_items_per_page", nbr_items_per_page)


def reset_items_per_page(mila_email_username):
    """
    Set the number of items to display by default for a specific user in a page
    presenting a list (such as a list of jobs, or a list of nodes) to the
    default value (arbitrarily defined by Clockwork's team).

    Parameters:
    mila_email_username     Element identifying the User in the users
                            collection of the database
    """
    # Call set_web_setting
    set_web_setting(
        mila_email_username, "nbr_items_per_page", default_nbr_items_per_page
    )


def enable_dark_mode(mila_email_username):
    """
    Enable the dark mode display option for a specific user.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
    """
    # Call set_web_setting
    set_web_setting(mila_email_username, "dark_mode", True)


def enable_dark_mode(mila_email_username):
    """
    Disable the dark mode display option for a specific user.

    Parameters:
        mila_email_username     Element identifying the User in the users
                                collection of the database
    """
    # Call set_web_setting
    set_web_setting(mila_email_username, "dark_mode", False)
