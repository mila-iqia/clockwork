# Running prometheus locally to try out things without corrupting the server at Mila

```
docker run --rm \
    -p 9090:9090 \
    --add-host=host.docker.internal:host-gateway \
    -v ${HOME}/Documents/code/slurm_monitoring_and_reporting/local_prometheus_fun/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
```

This is configured to fetch from `http://localhost:19997/books` and `http://localhost:19998/metrics`.

The goal is in part to find out how to use PromQL, to list the data available, to see what the requests look like.

Note that the `--add-host=host.docker.internal:host-gateway` line is to allow prometheus to 
connect to a script like `bibliotheque.py` that's running on the same machine but not inside
of a Docker container. This line comes from https://djangocas.dev/blog/docker-container-to-connect-localhost-of-host/#docker-for-linux, it runs on Linux, and they suggest variations for MacOS.