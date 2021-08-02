# Setup for Slurm Monitor

The Slurm Monitor is going to scrape the slurm information from various clusters
for the services described in "setup_four_services.md" : Prometheus, Grafana, ElasticSearch, MongoDB.

This requires three main elements of configuration:
    - a config file (see "demo_slurm_monitor_config.json"),
    - passwordless SSH access to the remote clusters,
    - scraper scripts installed on the remote clusters (usually by rsync).

Then we can launch one manual process for each cluster.

```bash
python3 -m slurm_monitor.main --port 17001 --cluster_name mila --endpoint_prefix "mila_" --refresh_interval 300
python3 -m slurm_monitor.main --port 17002 --cluster_name beluga --endpoint_prefix "beluga_" --refresh_interval 300
python3 -m slurm_monitor.main --port 17003 --cluster_name graham --endpoint_prefix "graham_" --refresh_interval 300
python3 -m slurm_monitor.main --port 17004 --cluster_name cedar --endpoint_prefix "cedar_" --refresh_interval 600
```


TODO : Talk about requirement to have SSH access.

TODO : Partition the config file from the scrapers.

TODO : Launch these in Docker containers.
