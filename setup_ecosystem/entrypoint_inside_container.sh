#!/bin/sh

# TL;DR: This is run from Docker compose. You don't run this manually.


# This script is made to be launched from within a Docker container,
# presumably one without all the libraries installed or the paths configured.
# It does not itself launch the container.
#
# For example, it should be running from "/clockwork/entrypoint_inside_container.sh".


# Not necessary because we'll be running from that directory.
# export PYTHONPATH=${PYTHONPATH}:"/clockwork"

cd /clockwork/web_server
python3 -m pip -r requirements.txt

export FLASK_RUN_PORT=5000
export FLASK_DEBUG=1
export FLASK_APP=main.py

# Note that, with the way that things are set up, when
# you end up here with Docker Compose, you should have
# the environment variables MONGO_INITDB_ROOT_USERNAME,
# and MONGO_INITDB_ROOT_PASSWORD set up.

## Your local mongodb instance.
# Note that the "@mongodb" mentioned in the connection string
# is the name of the host under Docker Compose.
# It seems that Docker Compose files refer to the addresses
# of services that way.
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@deepgroove.local:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"

# This is sufficient to disable the @login_required,
# but also to enable the /login/fake_user route.
export LOGIN_DISABLED=True

# local connections only
#    python3 -m flask run
# outside
python3 -m flask run --host=0.0.0.0