#!/bin/bash
set -eu

docker build -t clockwork_web clockwork_web
docker build -t clockwork_web_test clockwork_web_test
docker build -t clockwork_tools_test -f clockwork_tools_test/Dockerfile .
docker build -t slurm_state_test -f slurm_state_test/Dockerfile .

. ./env.sh

# This is to ensure that there aren't lingering containers after the test script exits.
trap "docker-compose down && docker-compose rm -fv" EXIT

docker-compose run clockwork_web_test
docker-compose run clockwork_tools_test
docker-compose run slurm_state_test
