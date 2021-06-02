# docker for prometheus-grafana-elasticsearch

| service | url | comment |
|---------|-----|---------|
| prometheus | http://deepgroove.local:9090 | web admin |
| grafana | http://deepgroove.local:3000 | web plots |
| elastic search | http://deepgroove.local:9200 | REST? |
| elastic search | http://deepgroove.local:9300 | open port in docker, but connections refused with web browser |
| mongodb | http://deepgroove.local:27017 | |

## docker commands

```
docker network create PrEsGr

# prometheus
docker run -d --name prometheus00 --net PrEsGr \
    -p 9090:9090 \
    --add-host=host.docker.internal:host-gateway \
    --volume ${HOME}/Documents/code/slurm_monitoring_and_reporting/local_prometheus_fun/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus

# grafana
docker run -d --name grafana00 --net PrEsGr \
    -p 3000:3000 \
    --user $(id -u ${USER}):$(id -g ${USER}) \
    --volume ${HOME}/Documents/code/slurm_monitoring_and_reporting/local_prometheus_fun/grafana_unprotected.ini:/etc/grafana/grafana.ini \
    grafana/grafana:latest-ubuntu

# elasticsearch
docker run -d --name elasticsearch00 --net PrEsGr \
	-p 9200:9200 -p 9300:9300 \
	-e "discovery.type=single-node" \
	elasticsearch:7.12.1

# mongodb
docker run -d --name mongodb00 --net PrEsGr \
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