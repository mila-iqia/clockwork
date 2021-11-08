#!/bin/bash
set -eu

docker build -t clockwork_web clockwork_web
docker build -t clockwork_web_test clockwork_web_test
docker build -t clockwork_tools_test -f clockwork_tools_test/Dockerfile .

export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@mongodb:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
# Any exterior port works, but let's pick 15000 to make it more unique
# and avoid some potential conflicts with other Flask servers on the
# host.

# At the same time, let's keep 5000 for services running inside the
# container to make it more predictible.
export FLASK_RUN_PORT=5000
export EXTERNAL_FLASK_RUN_PORT=15000

export clockwork_tools_test_HOST="clockwork_web-dev"
export clockwork_tools_test_PORT="${FLASK_RUN_PORT}"
export clockwork_tools_test_EMAIL="mario@mila.quebec"
export clockwork_tools_test_CLOCKWORK_API_KEY="000aaa"
export clockwork_tools_EMAIL=${clockwork_tools_test_EMAIL}
export clockwork_tools_API_KEY=${clockwork_tools_test_CLOCKWORK_API_KEY}

docker-compose -f setup_ecosystem/docker-compose.yml up -V --exit-code-from clockwork_web_test -- mongodb clockwork_web_test && docker-compose -f setup_ecosystem/docker-compose.yml rm -fv

docker-compose -f setup_ecosystem/docker-compose.yml up -V --exit-code-from clockwork_tools_test -- mongodb clockwork_tools_test && docker-compose -f setup_ecosystem/docker-compose.yml rm -fv
