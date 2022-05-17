#!/bin/bash
set -eu

coverage combine clockwork_web_test/.coverage clockwork_tools_test/.coverage slurm_state_test/.coverage scripts_test/.coverage
coverage report -m
