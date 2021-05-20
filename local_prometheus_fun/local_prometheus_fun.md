# Running prometheus locally to try out things without corrupting the server at Mila

```
docker run --rm \
    -p 9090:9090 \
    -v ${HOME}/Documents/code/slurm_monitoring_and_reporting/local_prometheus_fun/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
```

This is configured to fetch from `http://localhost:19997/books` and `http://localhost:19998/metrics`.

The goal is in part to find out how to use PromQL, to list the data available, to see what the requests look like.
