"""
We don't want to create the `app` in the global scope of "server_app.py"
because that would clash with our structure for testing.

We do need it to be somewhere, though, in the global scope of some file,
so that gcloud can run it with the equivalent of 
    entrypoint: gunicorn -b :$PORT main:app

That leads here, to this file, which is just a barebone launcher.
"""

import os
from server_app import create_app

"""
By default, we require only environment variable "MONGODB_CONNECTION_STRING"
to know how to connect to the mongodb database.

We would only disable logins manually when trying out certain
things locally, like doing development on the HTML/JS, and we
wanted to avoid authenticating with Google every time we relaunch.

We should pick some kind of convention by which, when we disable
the login, we set the user to be "mario" or something like that.
"""
app = create_app(
    extra_config={  "TESTING": False,
                    "LOGIN_DISABLED": os.environ.get("LOGIN_DISABLED", "False") in ["True", "true", "1"],
                    "MONGODB_CONNECTION_STRING": os.environ["MONGODB_CONNECTION_STRING"],
                    "MONGODB_DATABASE_NAME": os.environ.get("MONGODB_DATABASE_NAME", "clockwork")
    })

# If you call `app.run()` on the code that goes to gcloud, it causes problems.
# If you don't, then it's fine.
# app.run()