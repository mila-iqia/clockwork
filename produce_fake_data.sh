#!/bin/bash
set -eu

# Set the environnement
. ./env.sh
export CLOCKWORK_SLURM_REPORT_PATH="<insert_slurm_report_local_path>" # TODO

# This is to ensure that there aren't lingering containers after the test script exits.
trap "docker-compose down && docker-compose rm -fv" EXIT

# Run the Docker containers
docker-compose run clockwork_scripts
