# Slurm Scan

This is a rewrite of "slurm_monitor", which was itself based on the "sinfo.py" script.
Many factors have lead me to think that parsing the output of "sacct" and "sinfo" commands
is unfortunately the best that we can currently build on, given the unrealiability of PySlurm
when it comes to supporting the latest version of Slurm.

Moreover, I no longer support the idea of having the data scraping
and processing be done in the same script as the serving of
Prometheus endpoints (as well as populating of ElasticSearch).
There is a way to do all that, but without creating a monolithic script.

# dev notes

- Voir comment je gère mongoclient dans le web, et faire ça dans slurm_scan.

# TODO:

- Remove "alaingui" from the "remote_clusters_info.json".