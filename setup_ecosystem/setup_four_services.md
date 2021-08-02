# Setup for everything running locally, unprotected

This is a setup guide to have all the components running locally on your machine,
without authentication, in order to develop the code.

| service | exposed ports |
|--|--|
| Prometheus | 9090 |
| ElasticSearch | 9200, 9300 |
| Grafana | 3000 |
| MongoDB | 27017 |

When running in production, we would expect that Prometheus, ElasticSearch and MongoDB
be setup in a more robust way, with authentication and fault tolerance.
However, we still need a way to setup a development rig, hence this guide.

## Docker commands to start all the services

This starts daemons for all the services. It doesn't do anything useful with Prometheus,
ElasticSearch or Grafana, beyond simply starting the services and making it possible for
the code to interact with them.

Despite that, we have still exposed certain ports so that the developer might poke
the services, explore Prometheus, play with Grafana.


```bash
export DOCKER_NETWORK_NAME=PrEsGr
# write path for your own machine
export THIS_PROJECT_ROOT=${HOME}/Documents/code/slurm_monitoring_and_reporting_refactor

docker network create ${DOCKER_NETWORK_NAME}

# prometheus
docker run -d --name prometheus00 --net ${DOCKER_NETWORK_NAME} \
    -p 9090:9090 \
    --add-host=host.docker.internal:host-gateway \
    --volume ${THIS_PROJECT_ROOT}/setup_ecosystem/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus

# grafana
docker run -d --name grafana00 --net ${DOCKER_NETWORK_NAME} \
    -p 3000:3000 \
    --user $(id -u ${USER}):$(id -g ${USER}) \
    --volume ${THIS_PROJECT_ROOT}/setup_ecosystem/grafana_unprotected.ini:/etc/grafana/grafana.ini \
    grafana/grafana:latest-ubuntu

# elasticsearch
docker run -d --name elasticsearch00 --net ${DOCKER_NETWORK_NAME} \
	-p 9200:9200 -p 9300:9300 \
	-e "discovery.type=single-node" \
	elasticsearch:7.12.1

# mongodb
docker run -d --name mongodb00 --net ${DOCKER_NETWORK_NAME} \
	-p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=mongoadmin \
    -e MONGO_INITDB_ROOT_PASSWORD=secret_password_okay \
    mongo
```


## additional steps

Log into Grafana as admin/admin and skip changing password. Use `deepgroove.local:9090` as data source for Grafana.

Create database "slurm" with collections "jobs" and "nodes" in mongodb.
You can connect with Compass using the connection string
`mongodb://mongoadmin:secret_password_okay@deepgroove.local:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&ssl_cert_reqs=CERT_NONE&ssl=false`.

## some explanations

For Prometheus, `--add-host=host.docker.internal:host-gateway` is because we'll be reading from endpoints that run locally on the machine. We are actively working on those endpoints, and they are not inside a docker container. This is why we need to reach them like that. This line comes from https://djangocas.dev/blog/docker-container-to-connect-localhost-of-host/#docker-for-linux, it runs on Linux, and they suggest variations for MacOS.

The reason for mounting `prometheus.yml` is because we are going to actively work on it by adding endpoints and modifying the configuration. It would be inconvenient to have to modify it inside a container all the time.

For Grafana, `--user $(id -u ${USER}):$(id -g ${USER}) \` is just because the official container documentation told us to do it.

Mounting `grafana.ini` is so that we can activate the admin/admin account automatically to try out various dashboards without having to configure OAuth and address other production safety concerns.

For ElasticSearch, we copied the `-e "discovery.type=single-node"` from the official documentation.

It's not clear at the moment if we should be doing something with "/etc/elasticsearch/elasticsearch.yml" or if we'll be fine like that.

## short code snippet for elasticsearch that worked

This code worked on the setup described above. There was no need to setup anything else as far as authentication goes.

https://elasticsearch-py.readthedocs.io/en/7.10.0/

```python
>>> from datetime import datetime
>>> from elasticsearch import Elasticsearch
>>> es = Elasticsearch("http://deepgroove.local", port=9200)
>>> doc = {
...     'author': 'kimchy',
...     'text': 'Elasticsearch: cool. bonsai cool.',
...     'timestamp': datetime.now(),
... }
>>> res = es.index(index="test-index", id=1, body=doc)
>>> print(res['result'])
created
>>> res = es.get(index="test-index", id=1)
>>> print(res['_source'])
{'author': 'kimchy', 'text': 'Elasticsearch: cool. bonsai cool.', 'timestamp': '2021-05-28T00:30:20.451468'}
>>> es.indices.refresh(index="test-index")
{'_shards': {'total': 2, 'successful': 1, 'failed': 0}}
>>> res = es.search(index="test-index", body={"query": {"match_all": {}}})
>>> res
{'took': 42, 'timed_out': False, '_shards': {'total': 1, 'successful': 1, 'skipped': 0, 'failed': 0}, 'hits': {'total': {'value': 1, 'relation': 'eq'}, 'max_score': 1.0, 'hits': [{'_index': 'test-index', '_type': '_doc', '_id': '1', '_score': 1.0, '_source': {'author': 'kimchy', 'text': 'Elasticsearch: cool. bonsai cool.', 'timestamp': '2021-05-28T00:30:20.451468'}}]}}
>>> print("Got %d Hits:" % res['hits']['total']['value'])
Got 1 Hits:
>>> for hit in res['hits']['hits']:
...     print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
... 
2021-05-28T00:30:20.451468 kimchy: Elasticsearch: cool. bonsai cool.

```

## after power outage

You can do this once the containers have been created (as previously described).

Note that since we're in the development/prototyping stage, we are logging
all our data inside the containers, which means that we should probably not
wipe the containers and recreate them. Later on, we might want to take
a different approach and store the data in volume mounts.

```
docker start prometheus00
docker start grafana00
docker start elasticsearch00
docker start mongodb00
```