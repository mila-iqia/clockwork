# Slurm Scan

This is a rewrite of "slurm_monitor", which was itself based on the "sinfo.py" script.
Many factors have lead me to think that parsing the output of "sacct" and "sinfo" commands
is unfortunately the best that we can currently build on, given the unrealiability of PySlurm
when it comes to supporting the latest version of Slurm.

Moreover, I no longer support the idea of having the data scraping
and processing be done in the same script as the serving of
Prometheus endpoints (as well as populating of ElasticSearch).
There is a way to do all that, but without creating a monolithic script.

# `mila-automation` accounts

When running in production, we will use a special user account that does
not belong to a particular Mila member. Compute Canada has a special account
made for that purpose.

|cluster | automation account | who has access at the moment |
|--------|--------------------|------------------------------|
| mila   | ???                | guillaume alain |
| cedar  | mila-automation    | guillaume alain |
| beluga | mila-automation    | guillaume alain |
| graham | mila-automation    | guillaume alain |


# dev notes

- Voir comment je gère mongoclient dans le web, et faire ça dans slurm_scan.

# TODO:

- Remove "alaingui" from the "remote_clusters_info.json".

- One of the important things for clockwork_web_test is the fake_data.json.
However, when we update "slurm_state" according to a certain structure for
the slurm data, as returned by sacct/sinfo instead of pyslurm, then we
should update fake_data.json to reflect that structure.
This isn't hard, but it requires diligence.

- Share the access to "mila-automation" with Arnaud.
This should also be documented better in terms of which account should be
used for tools on what cluster.