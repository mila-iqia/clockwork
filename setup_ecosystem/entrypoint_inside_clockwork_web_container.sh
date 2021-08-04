#!/bin/sh

# Warning: This is run from within Docker compose. You don't run this manually.
#          It does not itself launch the container.


# You are going to run with the current filesystem layout inside the Docker container:
#
#   /clockwork/entrypoint_inside_clockwork_web_container.sh
#   /clockwork/clockwork_web
#   /clockwork/clockwork_web_test
#

export CLOCKWORK_ROOT="/clockwork"

export PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}
cd ${CLOCKWORK_ROOT}

python3 -m pip install --upgrade pip

python3 -m pip install -r ${CLOCKWORK_ROOT}/clockwork_web/requirements.txt
# do that for any other packages that we'll have in there
# python3 -m pip install -r ${CLOCKWORK_ROOT}/clockwork_web/requirements.txt

export FLASK_RUN_PORT=5000
export FLASK_DEBUG=1

export FLASK_APP=clockwork_web.main:app
# export FLASK_APP=main.py

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
    cd ${CLOCKWORK_ROOT}/clockwork_web_test
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




