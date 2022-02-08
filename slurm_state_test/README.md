# Slurm state test

## Overview

This folder gathers the implementation of a bunch of unit tests for Slurm state.
These tests can be launched through a Docker container, namely created by the
script `test.sh` at the top level of this Github repository.

## Structure

This section presents one **folder**, quickly described below.

| Folder | Content |
| -- | -- |
| files | Gather examples of scontrol reports for jobs and nodes, and a JSON describing a cluster for the tests |


Moreover, the following **files** are used to set up the scripts and provide data
to be based on.

| File | Use |
| -- | -- |
| Dockerfile | Dockerfile to create the image `slurm_state_test`. It is used by the `docker-compose` at the top level of the Github repository |
| requirements.txt | The Python installation requirements to set up the tests of slurm_state. It is namely used by the Dockerfile |
| fake_allocations_related_to_mila.json | Fake dictionary used in the tests |

Finally, the "tests" **files** chime in with the files of the `slurm_state` section.

| File | Use |
| -- | -- |
| test_anonymize_scontrol_report.py | Tests related to the anonymization of the scontrol report |
| test_extra_filters.py | Tests the additional filters defined in `../slurm_state/extra_filters.py` |
| test_mongo_client.py | Tests the connection to the database |
| test_mongo_update.py | Tests the update of jobs and nodes in the database |
| test_scontrol_parser.py | Tests the parser of the scontrol reports |

## Technologies

* Docker
* Python
* See `requirements.txt`.
