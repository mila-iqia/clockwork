#!/bin/bash
set -eu

docker build -t clockwork_web clockwork_web
docker build -t clockwork_web_test clockwork_web_test
docker build -t clockwork_tools_test -f clockwork_tools_test/Dockerfile .

. ./env.sh

export clockwork_tools_test_HOST=clockwork_web_test
docker-compose -f setup_ecosystem/docker-compose.yml up -V --exit-code-from clockwork_web_test -- clockwork_web_test && docker-compose -f setup_ecosystem/docker-compose.yml rm -fv

export clockwork_tools_test_HOST=clockwork_tools_test
docker-compose -f setup_ecosystem/docker-compose.yml up -V --exit-code-from clockwork_tools_test -- clockwork_tools_test && docker-compose -f setup_ecosystem/docker-compose.yml rm -fv
