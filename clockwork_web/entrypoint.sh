#!/bin/bash

# Compile the translation files
pybabel compile -f -d /clockwork/clockwork_web/static/locales

# Launch the Docker command if any
exec "$@"
