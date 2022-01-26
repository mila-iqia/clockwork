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
        L = list(mc["users"].find({"google_suite.email": auth["username"]}))

        if not L:
            return jsonify("Authorization error."), 401
        elif len(L) > 1:
            return jsonify("Database error."), 500

        D_user = L[0]
        if secrets.compare_digest(D_user["cw"]["clockwork_api_key"], auth["password"]):
            return f(*args, **kwargs, user_with_rest_auth=D_user)
        else:
            return jsonify("Authorization error."), 401

    return decorated
