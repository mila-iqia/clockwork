#!/bin/bash

docker build -t clockwork_web clockwork_web
docker build -t clockwork_web_test clockwork_web_test
docker build -t clockwork_tools_test clockwork_tools_test

. ./env.sh

export clockwork_tools_test_HOST="clockwork_dev"
docker-compose -f setup_ecosystem/docker-compose.yml run --service-ports clockwork_dev
