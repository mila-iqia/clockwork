#!/bin/bash

docker build -t clockwork_web clockwork_web
docker build -t clockwork_web_test clockwork_web_test

export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"

# Any exterior port works, but let's pick 15000 to make it more unique
# and avoid some potential conflicts with other Flask servers on the
# host.

# At the same time, let's keep 5000 for services running inside the
# container to make it more predictible.
export FLASK_RUN_PORT=5000
export EXTERNAL_FLASK_RUN_PORT=15000

export clockwork_tools_test_EMAIL="mario@mila.quebec"
export clockwork_tools_test_CLOCKWORK_API_KEY="000aaa"

docker-compose -f setup_ecosystem/docker-compose-test.yml up -V --exit-code-from clockwork_web_test -- mongodb clockwork_web_test
