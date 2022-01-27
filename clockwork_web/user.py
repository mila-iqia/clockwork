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
from flask_login import UserMixin, AnonymousUserMixin

import secrets

from .db import get_db


class User(UserMixin):
    """
    The methods of this class are determined by the demands of the
    `login_manager` library. For example, the fact that `get` returns
    a `None` if it fails to find the user.
    """

    def __init__(
        self,
        email,
        status,
        clockwork_api_key=None,
        mila_cluster_username=None,
        cc_account_username=None,
    ):
        """
        This constructor is called only by the `get` method.
        We never call it directly.
        """
        self.email = email
        self.status = status
        self.clockwork_api_key = clockwork_api_key
        self.mila_cluster_username = mila_cluster_username
        self.cc_account_username = cc_account_username

    # If we don't set those two values ourselves, we are going
    # to have users being asked to login every time they click
    # on a link or refresh the pages.
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.status == "enabled"

    def get_id(self):
        return self.email

    @staticmethod
    def get(email: str):
        """
        Returns the user with the specified email or None
        """

        mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]

        L = list(mc["users"].find({"mila_email_username": email}))
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
                email=e["mila_email_username"],
                status=e["status"],
                clockwork_api_key=e["clockwork_api_key"],
                mila_cluster_username=e["mila_cluster_username"],
                cc_account_username=e["cc_account_username"],
            )
            print("Retrieved entry for user with email %s." % user.email)

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
        mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        res = mc["users"].update_one(
            {"mila_email_username": self.email},
            {"$set": {"clockwork_api_key": self.clockwork_api_key}},
        )
        if res.modified_count != 1:
            self.clockwork_api_key = old_key
            raise ValueError("could not modify api key")


class AnonUser(AnonymousUserMixin):
    def __init__(self):
        self.name = "Anonymous"
        self.email = "anonymous@mila.quebec"
        self.status = "enabled"
        self.clockwork_api_key = "deadbeef"
        self.cc_account_username = None
        self.mila_cluster_username = None

    def new_api_key(self):
        # We don't want to touch the database for this.
        self.clockwork_api_key = secrets.token_hex(32)
