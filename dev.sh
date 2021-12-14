#!/bin/bash

set -eu

docker build -t clockwork_dev -f clockwork_dev.Dockerfile .

. ./env.sh

# Make sure to cleanup on exit
trap "docker-compose down && docker-compose rm -fv" EXIT

docker-compose run --service-ports clockwork_dev
