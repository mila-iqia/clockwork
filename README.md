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
* clockwork_tools_test : unit tests for "clockwork_tools", running on a dev instance of "clockwork_web"

* slurm_state : internal tools to parse the slurm reports from many clusters
* scripts : useful scripts for occasional uses internally
* docs : documentation for this project, to be published externally

Needs to be redesigned or deleted:

* setup_ecosystem : launch point for web server, for tests and development. needs refactoring.


## Summary of who runs what where

| component | launched by | target audience | runs against which clockwork_web |
|--|--|--|--|
| clockwork_web | IDT | everyone at Mila | N/A |
| clockwork_web_test | IDT | IDT | dev instance in docker container |
| clockwork_tools | N/A | everyone at Mila  | prod |
| clockwork_tools_test | IDT | IDT | dev instance in docker container|

## modules needed

```bash
# for main project
python3 -m pip install flask flask-login numpy pymongo oauthlib
# for docs
python3 -m pip install sphinx myst_parser sphinx_rtd_theme sphinxcontrib.httpdomain
```

## documentation

In the "doc" directory, build the documentation with `make rst; make html`.