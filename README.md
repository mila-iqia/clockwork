# A Clockwork Cluster

Many of the "readme" files are outdate, but still contain useful pieces,
and the final layout/functionality of this repo are not known yet, so that
makes it hard to document properly.

The most relevant readme file is
[setup_ecosystem/docker-compose.yml !](https://github.com/mila-iqia/clockwork/blob/master/setup_ecosystem/docker-compose.yml)
and we can see how to use it by looking at the various `.sh` files
in the top level of this repo.

## Brief overview of folders

Used:

* clockwork_web : the web server, to be deployed by IDT
* clockwork_web_test : unit tests for "clockwork_web"

* clockwork_tools : python module to be used by Mila members in conjuction with prod instance "clockwork_web"
* clockwork_tools_test : unit tests for "clockwork_tools"

* slurm_state : internal tools to parse the slurm reports from many clusters
* slurm_state_test : unit tests for "slurm_state"

* test_common : some functions used by two or more of the "_test" components

* scripts : useful scripts for occasional uses internally
* docs : documentation for this project, to be published externally

* setup_ecosystem : configuration to launch the web server, tests and development instances. Needs refactoring.


## Summary of who runs what where

| component | launched by | target audience | runs against which clockwork_web |
|--|--|--|--|
| clockwork_web | IDT | everyone at Mila | N/A |
| clockwork_web_test | IDT | IDT | dev instance in docker container |
| clockwork_tools | N/A | everyone at Mila  | prod |
| clockwork_tools_test | IDT | IDT | dev instance in docker container |
| slurm_state | IDT | IDT | mongodb instance (dev or prod) |
| slurm_state_test | IDT | IDT | dev instance in docker container |

## modules needed

```bash
# for main project
python3 -m pip install flask flask-login numpy pymongo oauthlib coverage black ldap3 toml
# for docs
python3 -m pip install sphinx myst_parser sphinx_rtd_theme sphinxcontrib.httpdomain
```

## documentation

In the "doc" directory, build the documentation with
```
export CLOCKWORK_CONFIG=../test_config.toml
make rst
make html
```

## running the code in "dev" mode inside a Docker container

Start the container:
```
bash dev.sh
```
Inside the container:
```
python3 scripts/store_fake_data_in_db.py
python3 -m flask run --host="0.0.0.0"
```
Navigate to `http://localhost:15000` on your computer.
