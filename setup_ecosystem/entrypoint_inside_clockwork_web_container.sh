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
python3 -m pip install -r ${CLOCKWORK_ROOT}/clockwork_web_test/requirements.txt
python3 -m pip install -r ${CLOCKWORK_ROOT}/clockwork_tools/requirements.txt
python3 -m pip install -r ${CLOCKWORK_ROOT}/clockwork_tools_test/requirements.txt

export FLASK_APP=clockwork_web.main:app

# Note that, with the way that things are set up, when
# you end up here with Docker Compose, you should have
# the environment variables MONGO_INITDB_ROOT_USERNAME,
# and MONGO_INITDB_ROOT_PASSWORD set up.

## Your local mongodb instance.
# Note that the "@mongodb" mentioned in the connection string
# is the name of the host under Docker Compose.
# It seems that Docker Compose files refer to the addresses
# of services that way.
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@mongodb:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"

# Environment variable that will decide whether we're going to run
# the tests or run in development mode.
# We'll give it a default value to run only the unit tests.
# export CLOCKWORK_TASK=${CLOCKWORK_TASK:-"clockwork_run_web_test"}

if [ ${CLOCKWORK_TASK} = "clockwork_run_web_test" ]; then
    # This is sufficient to disable the @login_required,
    # but also to enable the /login/fake_user route.
    export LOGIN_DISABLED=True
    # These tests are run without instantiating the web server
    # as a separate program.
    cd ${CLOCKWORK_ROOT}/clockwork_web_test
    pytest
elif [ ${CLOCKWORK_TASK} = "clockwork_run_clockwork_tools_test" ]; then
    export FLASK_DEBUG=1
    # This is sufficient to disable the @login_required,
    # but also to enable the /login/fake_user route.
    export LOGIN_DISABLED=True
    # Gotta start the server if you expect to run tests
    # with your tools interacting with it.
    python3 -m flask run --host=0.0.0.0 &
    sleep 2

    # note the "TEST_" being removed
    export clockwork_tools_EMAIL=${clockwork_tools_test_EMAIL}
    export clockwork_tools_API_KEY=${clockwork_tools_test_CLOCKWORK_API_KEY}
    cd ${CLOCKWORK_ROOT}/clockwork_tools_test
    pytest
elif [ ${CLOCKWORK_TASK} = "clockwork_run_web_development" ]; then
    export FLASK_DEBUG=1
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
    export FLASK_DEBUG=0  # is this how it works or should I unset it?
fi




