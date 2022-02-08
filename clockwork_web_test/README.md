# Clockwork web tests

## Overview

This folder gathers the implementation of a bunch of unit tests for Clockwork
web. These tests can be launched through a Docker
container, namely created by the script `test.sh` at the top level of this
Github repository.

## Structure

The different files of this folder are presented below. They are listed through
four categories:
* the "Common files" are the files used to set up the tests
* the "Common tests" test the functions destined to both the REST API
and the web interface
* the "REST API tests" test the functions exclusively related to the REST API
* the "Web interface tests" test the functions exclusively related to the web
interface.

### Common files

| File | Content |
| -- | -- |
| Dockerfile | Dockerfile used to create the image `clockwork_web_test` |
| conftest.py | Create and configure tests instances|
| requirements.txt | Gathers the Python requirements in order to launch these tests |

### Common tests

| File | Content |
| -- | -- |
| test_db.py | Tests some jobs insertion and deletion operations applied on the database in order to check the connection with it |
| test_dev.py | Test to check if the environment is up |
| test_login_routes.py | Tests the OAuth workflow used for login to the site |
| test_read_mila_ldap.py | Tests the update of users in the database, from Mila LDAP information |

### REST API tests

| File | Content |
| -- | -- |
| test_rest_authentication.py | Tests the authentication fails for the REST API |
| test_rest_jobs.py | Tests the REST API requests related to the jobs |
| test_rest_nodes.py | Tests the REST API requests related to the nodes |

### Web interface tests

| File | Content |
| -- | -- |
| test_browser_jobs.py | Tests the rendering of jobs information on the web interface |
| test_browser_nodes.py | Tests the rendering of nodes information on the web interface |
| test_browser_settings.py | Tests the rendering of the "Settings" page |

## Technologies

* Docker
* Python
* See `requirements.txt`.
