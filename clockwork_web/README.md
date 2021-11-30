# Clockwork cluster web server

## How to run locally (no authentication)

[THIS IS OBSOLETE.]

You can run this with your own python environment, either with
your own instance of a mongodb server, or with the same one
on Atlas that the Google Cloud deployment uses.

It exposes a special route `/login/fake_user` that sets the current_user
to something that allows for easier development of the routes
that require some kind of user in order to matter (e.g. user settings).

```bash
export FLASK_RUN_PORT=5550
export FLASK_DEBUG=1
export FLASK_APP=main.py

## the Atlas mongodb
# export MONGODB_CONNECTION_STRING="don't commit this to github"
# export MONGODB_DATABASE_NAME="clockwork"

## your local mongodb instance
export MONGODB_CONNECTION_STRING="don't commit this to github"
export MONGODB_DATABASE_NAME="clockwork"

# This is sufficient to disable the @login_required,
# but also to enable the /login/fake_user route.
export LOGIN_DISABLED=True

# local connections only
#    python3 -m flask run
# outside
python3 -m flask run --host=0.0.0.0
```
