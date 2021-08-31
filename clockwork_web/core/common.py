
from flask import request
from flask_login import current_user


def get_filter_from_request_args(keys_for_filter: list):
    """
    Helper function. Relies on `request` in the correct context
    in order to get the actual values.
    """
    filter = {}
    for k in keys_for_filter:
        v = request.args.get(k, None)
        if v is not None:
            filter[k] = v
    return filter

def get_mila_email_username():
    # When running tests against routes protected by login (under normal circumstances),
    # `current_user` is not specified, so retrieving the email would lead to errors.
    if hasattr(current_user, "email"):
        return current_user.email.split("@")[0]
    else:
        return None