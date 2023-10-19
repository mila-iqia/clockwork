"""
Every call to a REST API endpoint has to be validated in terms of email:clockwork_api_key.

The reason why we don't pass authentication information through json contents
in the body is that
- it requires a json-deserialization of potentially-malicious contents
- it works only for POST (not a big deal)

"""

import re
import base64
from functools import wraps
import secrets
import logging

from flask import g
from flask.globals import current_app
from flask import request
from flask.json import jsonify

from ..db import get_db


def authentication_required(f):
    """Checks for HTTP Authentication for json endpoints."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth is None:
            logging.warning("REST authentication error : no authorization in request")
            return jsonify("Authorization error."), 401

        mc = get_db()
        L = list(mc["users"].find({"mila_email_username": auth["username"]}))

        if not L:
            logging.warning(
                f"REST authentication error : user {auth['username']} not in database"
            )
            return jsonify("Authorization error."), 401
        elif len(L) > 1:
            logging.warning(
                f"REST authentication error : database error (user {auth['username']} present {len(L)} times in database)"
            )
            return jsonify("Database error."), 500

        D_user = L[0]
        if D_user["clockwork_api_key"] is not None and secrets.compare_digest(
            D_user["clockwork_api_key"], auth["password"]
        ):
            g.current_user_with_rest_auth = D_user
            return f(*args, **kwargs)
            # no need to manually clear `g.current_user_with_rest_auth` because
            # it gets cleared when the app context pops
        else:
            logging.warning(
                f"REST authentication error : bad key (user {auth['username']})"
            )
            return jsonify("Authorization error."), 401

    return decorated
