"""
Determines what the properties of the "User" are going to be.

TODO : This is broken but we don't currently use the web interface
so we don't interact with it that way. See CW-85.

TODO : There are rough edges here because of decisions pertaining
to the correct behavior to have when encountering errors.
For example, what are we supposed to do when we find two instances
of a user in our database?

This file could be polished a little better once we have more
of the project in place and we can make more informed decisions
about these things.
"""

from flask.globals import current_app
from flask import session
from flask_login import UserMixin, AnonymousUserMixin
from flask_babel import gettext

import secrets

from .db import get_db
from clockwork_web.core.users_helper import (
    enable_dark_mode,
    disable_dark_mode,
    set_items_per_page,
    get_default_setting_value,
    set_language,
)


class User(UserMixin):
    """
    The methods of this class are determined by the demands of the
    `login_manager` library. For example, the fact that `get` returns
    a `None` if it fails to find the user.
    """

    def __init__(
        self,
        mila_email_username,
        status,
        clockwork_api_key=None,
        mila_cluster_username=None,
        cc_account_username=None,
        cc_account_update_key=None,
        web_settings=None,
    ):
        """
        This constructor is called only by the `get` method.
        We never call it directly.
        """
        self.mila_email_username = mila_email_username
        self.status = status
        self.clockwork_api_key = clockwork_api_key
        self.mila_cluster_username = mila_cluster_username
        self.cc_account_username = cc_account_username
        self.cc_account_update_key = cc_account_update_key
        self.web_settings = {}
        if web_settings is None:
            self.web_settings["nbr_items_per_page"] = get_default_setting_value(
                "nbr_items_per_page"
            )
            self.web_settings["dark_mode"] = get_default_setting_value("dark_mode")
            self.web_settings["language"] = get_default_setting_value("language")
        else:
            self.web_settings["nbr_items_per_page"] = web_settings["nbr_items_per_page"]
            self.web_settings["dark_mode"] = web_settings["dark_mode"]
            self.web_settings["language"] = web_settings["language"]

    # If we don't set those two values ourselves, we are going
    # to have users being asked to login every time they click
    # on a link or refresh the pages.
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.status == "enabled"

    def get_id(self):
        return self.mila_email_username

    @staticmethod
    def get(mila_email_username: str):
        """
        Returns the user with the specified email or None
        """

        mc = get_db()

        L = list(mc["users"].find({"mila_email_username": mila_email_username}))
        # This is not an error from which we expect to be able to recover gracefully.
        # It could happen if you copied data from your database directly
        # using an external script, and ended up with many instances of your users.
        # In that case, you might have other issues as well, so let's not even try
        # to just return the first instance of that user (ignoring the rest),
        # because that might hide more problems downstream.
        if len(L) not in [0, 1]:
            print("Found %d users with email %s. This can't happen." % (len(L), email))
            return None
        elif len(L) == 0:
            return None
        else:
            e = L[0]
            user = User(
                mila_email_username=e["mila_email_username"],
                status=e["status"],
                clockwork_api_key=e["clockwork_api_key"],
                mila_cluster_username=e["mila_cluster_username"],
                cc_account_username=e["cc_account_username"],
                cc_account_update_key=e["cc_account_update_key"],
                web_settings=e["web_settings"],
            )
            print("Retrieved entry for user with email %s." % user.mila_email_username)

            # Note that, at this point, it might be the case that the returned
            # user has status "disabled". The parent code will have to refrain
            # from continuing further if that's the case.
            return user

    def new_api_key(self):
        """
        Create a new API key and save it to the database.
        """
        old_key = self.clockwork_api_key
        self.clockwork_api_key = secrets.token_hex(32)
        mc = get_db()
        res = mc["users"].update_one(
            {"mila_email_username": self.mila_email_username},
            {"$set": {"clockwork_api_key": self.clockwork_api_key}},
        )
        if res.modified_count != 1:
            self.clockwork_api_key = old_key
            raise ValueError(gettext("could not modify api key"))

    def new_update_key(self):
        """
        Create a new API key and save it to the database.
        """
        self.cc_account_update_key = secrets.token_hex(32)
        mc = get_db()
        res = mc["users"].update_one(
            {"mila_email_username": self.mila_email_username},
            {"$set": {"cc_account_update_key": self.cc_account_update_key}},
        )
        if res.modified_count != 1:
            raise ValueError(gettext("could not modify update key"))

    ###
    #   Web settings
    ###
    def settings_dark_mode_enable(self):
        """
        Enable the dark mode display option for the User.

        Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
        """
        return enable_dark_mode(self.mila_email_username)

    def settings_dark_mode_disable(self):
        """
        Disable the dark mode display option for the User.

        Returns:
            A tuple containing
            - a HTTP status code (it should only return 200)
            - a message describing the state of the operation
        """
        return disable_dark_mode(self.mila_email_username)

    def settings_nbr_items_per_page_set(self, nbr_items_per_page):
        """
        Set a new value to the preferred number of items to display per page for
        the current user.

        Parameters:
        - nbr_items_per_page    The preferred number of items to display per
                                page for the User, ie the value to save in
                                its settings

        Returns:
            A tuple containing
            - a HTTP status code (200 or 400)
            - a message describing the state of the operation
        """
        return set_items_per_page(self.mila_email_username, nbr_items_per_page)

    def settings_language_set(self, language):
        """
        Set a preferred language for the current user.

        Parameters:
        - language      The language chosen by the user to interact with. The
                        available languages are listed in the configuration file.

        Returns:
            A tuple containing
            - a HTTP status code (200 or 400)
            - a message describing the state of the operation
        """
        return set_language(self.mila_email_username, language)

    def get_language(self):
        return self.web_settings["language"]


class AnonUser(AnonymousUserMixin):
    def __init__(self):
        self.mila_email_username = "anonymous@mila.quebec"
        self.status = "enabled"
        self.clockwork_api_key = "deadbeef"
        self.cc_account_username = None
        self.mila_cluster_username = None
        self.cc_account_update_key = None
        self.web_settings = {}
        self.web_settings["nbr_items_per_page"] = get_default_setting_value(
            "nbr_items_per_page"
        )
        self.web_settings["dark_mode"] = get_default_setting_value("dark_mode")
        self.web_settings["language"] = None

    def new_api_key(self):
        # We don't want to touch the database for this.
        self.clockwork_api_key = secrets.token_hex(32)

    def settings_dark_mode_enable(self):
        """
        Enable the dark mode display option for the User.

        Returns:
        A tuple containing
        - a HTTP status code (it should only return 200)
        - a message describing the state of the operation
        """
        try:
            self.web_settings["dark_mode"] = True
            return (200, gettext("The dark_mode has been enabled."))
        except Exception as e:
            return (500, gettext("An error occurred."))

    def settings_dark_mode_disable(self):
        """
        Disable the dark mode display option for the User.

        Returns:
            A tuple containing
            - a HTTP status code (it should only return 200)
            - a message describing the state of the operation
        """
        try:
            self.web_settings["dark_mode"] = False
            return (200, gettext("The dark_mode has been disabled."))
        except Exception as e:
            return (500, gettext("An error occurred."))

    def get_language(self):
        return self.web_settings["language"]
