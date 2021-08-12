"""
Every call to a REST API endpoint has to be validated in terms of email:clockwork_api_key.

The reason why we don't pass authentication information through json contents
in the body is that
    - it requires a json-deserialization of potentially-malicious contents
    - it works only for POST (not a big deal)

"""

import re
import base64

from flask.globals import current_app

from ..db import get_db


def authenticate_with_header_basic(s:str):
    """
    Looks at the value of {"Authorization" : "Basic kfjio329ur328jb"},
    decodes and analyzes the string,
    compares against database, verifies that it matches,
    return the user information from the database (as dict) if it matches,
    and None otherwise.

    With this example, the argument `s` takes the value "Basic kfjio329ur328jb".
    """
    E = _split_header_authorization_value(s)
    if E is None:
        return None

    mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
    # We could match against `'clockwork_api_key': E['clockwork_api_key']` in the same query,
    # but it would be interesting to log attempts in which a correct email was given
    # with the wrong clockwork_api_key. For debugging purposes, mostly, but also as a way
    # to see whose accounts are being targeted for clockwork_api_key being guessed.
    #
    # Note that we don't want to give feedback to the users about why their authentication
    # failed that might help attackers. That being said, most accounts aren't very secret
    # because students have their @mila.quebec emails listed online.

    L = list(mc["users"].find({'email': E['email']}))
    if L:
        # If the user is present, we expect only one entry, but it's not worth
        # shutting down the web server for such an error.
        if 1 < len(L):
            current_app.logger.error(f"You have many entries in the database matching {E}.")

        D_user = L[0]
        if D_user['clockwork_api_key'] == E['clockwork_api_key']:
            # success
            return D_user
        else:
            current_app.logger.debug(f"Wrong clockwork_api_key {E['clockwork_api_key']} for {E['email']}")
            # failure to authenticate
            return None
    else:
        current_app.logger.debug(f"Found no user with email {E['email']}.")
        # failure to authenticate
        return None



def _split_header_authorization_value(s:str) -> dict:
    """
    Helper for `authenticate` separated for easier unit testing.

    Returns a dict if successful, and `None` otherwise.
    """
    # Caret for beginning, dollar for ending.
    if m := re.match("^Basic\s+(.*?)$", s):
        decoded_bytes = base64.b64decode(m.group(1))
        decoded_s = str(decoded_bytes, "utf-8")
    else:
        return None

    # Here "decoded_s" should be something like "guillaume.alain@mila.quebec:98rjfjksdfkjsdh".

    if m := re.match("^(.*):(.*)$", decoded_s):
        email = m.group(1)
        clockwork_api_key = m.group(2)
        return {'email': email, 'clockwork_api_key': clockwork_api_key}
    else:
        return None



#def test():
#    _split_header_authorization_value("Basic kfjio329ur328jb")