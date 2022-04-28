#!/bin/bash
set -eu

SLURM_REPORT_PATH=$1

if [ -d "$SLURM_REPORT_PATH" ]; then
    # Set the environnement
    . ./env.sh
    export CLOCKWORK_SLURM_REPORT_PATH=$SLURM_REPORT_PATH

    # This is to ensure that there aren't lingering containers after the test script exits.
    trap "docker-compose down && docker-compose rm -fv" EXIT

    # Run the Docker containers
    docker-compose run clockwork_scripts
else
    echo "The directory $SLURM_REPORT_PATH has not been found."
fi
