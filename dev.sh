#!/bin/bash

set -eu

docker build -t clockwork_dev -f setup_ecosystem/clockwork_dev.Dockerfile .

. ./env.sh

docker-compose -f setup_ecosystem/docker-compose.yml run --service-ports clockwork_dev

docker-compose -f setup_ecosystem/docker-compose.yml down && docker-compose -f setup_ecosystem/docker-compose.yml rm -fv
