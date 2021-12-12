#!/bin/bash

set -eu

docker build -t clockwork_dev -f clockwork_dev.Dockerfile .

. ./env.sh

docker-compose run --service-ports clockwork_dev

docker-compose down && docker-compose rm -fv
