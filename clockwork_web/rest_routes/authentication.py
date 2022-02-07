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
            return jsonify("Authorization error."), 401

        mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        L = list(mc["users"].find({"mila_email_username": auth["username"]}))

        if not L:
            return jsonify("Authorization error."), 401
        elif len(L) > 1:
            return jsonify("Database error."), 500

        D_user = L[0]
        if secrets.compare_digest(D_user["clockwork_api_key"], auth["password"]):
            return f(*args, **kwargs)
            # no need to manually clear `g.user_with_rest_auth` because
            # it gets cleared when the app context pops
        else:
            return jsonify("Authorization error."), 401

    return decorated
