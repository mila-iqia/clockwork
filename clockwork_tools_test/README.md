# Clockwork tools tests

## Overview

This folder gathers the implementation of a bunch of unit tests for Clockwork
tools. These tests can be launched through a Docker
container, namely created by the script `test.sh` at the top level of this
Github repository.

## Structure

This folder presents the following files:

| File | Content |
| -- | -- |
| Dockerfile | Dockerfile used to create the image `clockwork_tools_test` |
| conftest.py | Define the possible configurations for the tests |
| requirements.txt | Gathers the Python requirements in order to launch these tests |
| test_mt_jobs.py | Tests related to the jobs information retrieval |
| test_mt_nodes.py | Tests related to the nodes information retrieval |

## Technologies

* Docker
* Python
* See `requirements.txt`
