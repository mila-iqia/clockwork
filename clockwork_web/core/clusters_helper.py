"""
Helper function regarding the clusters.
"""


def get_all_clusters():
    """
    List all the clusters.

    Returns:
        A list of the clusters' names
    """
    # TODO: Retrieve infos from TOML configuration file
    return {
        "beluga": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": "America/Montreal",
            "nbr_cpus": 1950,  # Number of CPUs on this cluster
            "nbr_gpus": 696,  # Number of GPUs on this cluster
            "links": {
                "alliance": "https://docs.alliancecan.ca/wiki/B%C3%A9luga/",
                "mila": "https://docs.mila.quebec/Extra_compute.html#beluga",
            },
        },
        "cedar": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": "America/Vancouver",
            "nbr_cpus": 4948,  # Number of CPUs on this cluster
            "nbr_gpus": 1352,  # Number of GPUs on this cluster
            "links": {
                "alliance": "https://docs.alliancecan.ca/wiki/Cedar",
                "mila": "https://docs.mila.quebec/Extra_compute.html#cedar",
            },
        },
        "graham": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": "America/Toronto",
            "nbr_cpus": 2660,  # Number of CPUs on this cluster
            "nbr_gpus": 536,  # Number of GPUs on this cluster
            "links": {
                "alliance": "https://docs.alliancecan.ca/wiki/Graham",
                "mila": "https://docs.mila.quebec/Extra_compute.html#graham",
            },
        },
        "mila": {
            "organism": "Mila",
            "timezone": "America/Montreal",
            "nbr_cpus": 4860,  # Number of CPUs on this cluster
            "nbr_gpus": 532,  # Number of GPUs on this cluster
            "links": {"mila": "https://docs.mila.quebec/Information.html"},
        },
        "narval": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": "Unknown",
            "nbr_cpus": 2608,  # Number of CPUs on this cluster
            "nbr_gpus": 636,  # Number of GPUs on this cluster
            "links": {"alliance": "https://docs.alliancecan.ca/wiki/Narval"},
        },
    }  # TODO: centralize
