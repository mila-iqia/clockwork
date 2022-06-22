"""
Helper functions in order to handle User information.
"""

from clockwork_web.db import get_db

def get_user(username):
    """
    Get information of a specific user defined by its name.

    Parameters:
        username   Name of the requested user

    Returns:
        A dictionary describing the requested user if it has been found.
        An empty dictionary otherwise
    """
    # Check the username type
    if username and isinstance(username, str):
        # Retrieve the database
        db = get_db()
        # Find one entry presenting the Mila address associated to the username
        # as mila_email_username
        requested_mila_email_username = "{}@mila.quebec".format(username)
        found_user = db["users"].find_one(
            {"mila_email_username": requested_mila_email_username}, # The filter we apply to find the user
            {"_id": 0} # The '_id' element is not returned in the user's info
        )
        # Return the found user
        if found_user is not None:
            return found_user

    # By default, return an empty dictionary
    return {}
