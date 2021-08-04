#!/bin/sh

# TL;DR: This is run from Docker compose. You don't run this manually.


# This script is made to be launched from within a Docker container,
# presumably one without all the libraries installed or the paths configured.
# It does not itself launch the container.
#
# For example, it should be running from "/clockwork/entrypoint_inside_clockwork_web_container.sh".


# Not necessary because we'll be running from that directory.
# export PYTHONPATH=${PYTHONPATH}:"/clockwork"

cd /clockwork/web_server
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

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

# Environment variable that will decide whether we're going to run
# the tests or run in development mode.
# We'll give it a default value to run only the unit tests.
# export CLOCKWORK_TASK=${CLOCKWORK_TASK:-"clockwork_run_web_unit_tests"}

if [ ${CLOCKWORK_TASK} = "clockwork_run_web_unit_tests" ]; then
    # This is sufficient to disable the @login_required,
    # but also to enable the /login/fake_user route.
    export LOGIN_DISABLED=True
    cd /clockwork/web_server
    pytest
elif [ ${CLOCKWORK_TASK} = "clockwork_run_web_development" ]; then
    # This is sufficient to disable the @login_required,
    # but also to enable the /login/fake_user route.
    export LOGIN_DISABLED=True
    python3 -m flask run --host=0.0.0.0
elif [ ${CLOCKWORK_TASK} = "clockwork_run_web_production" ]; then
    # TODO : Run gunicorn with the proper settings.
    #        This isn't hard to do, but it's not worth getting
    #        in that rabbit hole right now.
    #        We can't test it without DNS, TLS, nginx setup anyway.
    echo "CLOCKWORK_TASK 'clockwork_run_web_production' not currently implemented."
fi




