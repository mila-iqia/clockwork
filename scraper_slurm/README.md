# Scraper Slurm

## two types of data scrapers

There are two kinds of scraper scripts:
    - scripts using PySlurm on clusters (best)
    - scripts calling `sinfo` and `sacct`, then parsing the output (okay)

We get a lot more data fields from using PySlurm. It is more robust in the sense
that other people (PySlurm devs) are making sure that the data from Slurm
is imported properly into Python, but it is also more exposed to the possibility
that an upgrade to Slurm will break the support for PySlurm.

The fallback option is the script that we wrote, which parses the stdout
from `sinfo` and `sacct`, and then harmonizes the returned value to those
exposed PySlurm. This leaves out many fields unfilled, but all the crucial fields
should be covered.

## where does the data go?

The data being scraped from the clusters will be sent to three services:
    - MongoDB
    - Prometheus
    - ElasticSearch

Technically, Prometheus pulls from endpoints that we'll expose so we don't "send"
the data in the same way as for the other two services.

The scraper script is told about these services through environment variables.
This makes it possible to run them on different machines, or also to omit some
of them.

The main use for Prometheus and ElasticSearch are to be data sources for a Grafana server.
The data in MongoDB is used by the "Clockwork Cluster" web front-end,
which is contained in this Github repo but doesn't share any of the code.

## diagram of components

TODO : Sketch something here to illustrate the fact that one of the scripts
       is to be copied over to the cluster itself, and how we interact with
       prometheus and elasticsearch.

## scripts calling PySlurm

This is the favored options, but it depends on support for PySlurm on the target clusters.
This works for certain versions of Slurm, but not the latest, unfortunately.

TODO : Name the file name here.

## scripts calling `sinfo` and `sacct`

TODO : Name the file name here.


# Mongodb

TODO : Describe environment variables.
TODO : Describe how to launch in Docker.

# Prometheus

TODO : Describe environment variables.
TODO : Describe how to launch in Docker.

# ElasticSearch

TODO : Describe environment variables.
TODO : Describe how to launch in Docker.

# Installing PySlurm

## slurm versions

There are difficulties due to the fact that PySlurm is a project downstream from Slurm.
Most recent versions of Slurm are not necessarily supported, so we have to
anticipate this on our cluster and those of Compute Canada.

| cluster | slurm version | slurm installation path | pyslurm that worked |
|---|---|---|---|
| beluga | 19.05.8 | /opt/software/slurm | 19.05.0 |
| graham | 20.02.4 | /opt/software/slurm |
| cedar | 20.11.4 | /opt/software/slurm |
| mila | 19.05.2 | /opt/slurm | 19.05.0 |

Note that there is an environment variable `$SLURM_HOME`
that gives the slurm installation path. Other versions of Slurm
can be found in nearby directories, but keep in mind that
if you compile PySlurm against a version of Slurm that is
different from the one deployed and running on the cluster,
your calls to PySlurm will not succeed.


## installation procedure

```bash
module load python/3.8.2
python3 -m pip install --user Cython numpy
```

```bash
# this works on `monitoring` that has slurm installed at `/opt/software/slurm`
cd ${HOME}/Documents/code
git clone https://github.com/PySlurm/pyslurm.git
cd pyslurm
# You need to checkout a version that's compatible
# with the not-recent version of slurm installed on our cluster.
# We do this because of the error message
#    "ERROR: Build - Incorrect slurm version detected, requires Slurm 20.02"
# that we get if we don't use a previous verison.
git checkout 19.05.0
python3 setup.py build --slurm=/opt/software/slurm
python3 setup.py install --user
```

## special case for Graham cluster

This required modifying a line from the PySlurm code.

```bash
module load python/3.6.10 
python3 -m pip install --user Cython

cd ${HOME}/Documents/code
rm -rf pyslurm
git clone https://github.com/PySlurm/pyslurm.git
cd pyslurm
# then you need to edit out (or comment out)
# one line from  pyslurm/pydefines/slurm_defines.pxi
# ##NO_CONSUME_VAL64 = slurm.NO_CONSUME_VAL64

# /opt/software/slurm/20.02.4/
python3 setup.py build --slurm=$SLURM_HOME
python3 setup.py install --user
```