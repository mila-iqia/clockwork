"""
Helper functions related to the clusters.
"""

from slurm_state.config import (
    get_config,
    string,
    optional_string,
    string_list,
    integer,
    timezone,
    SubdictValidator,
    register_config,
)


def alloc_valid(value):
    """
    Check if the "allocations" field of a cluster is either "*" or a list of
    strings

    Parameters:
        - value     The value of the field "allocations" for a cluster in the
                    configuration file
    """
    if value == "*":
        return value
    return string_list(value)


def _load_clusters_from_config():
    """
    Import the clusters from the config file
    """
    # Define the format of a cluster
    clusters_valid = SubdictValidator({})
    # Global information
    clusters_valid.add_field("organization", optional_string, default=False)
    clusters_valid.add_field("timezone", timezone)
    # Allocations information
    clusters_valid.add_field(
        "account_field", string
    )  # This is the name of a MongoDB field that will be used to store the account name for each user on this cluster.
    clusters_valid.add_field(
        "update_field", optional_string
    )  # This is the name of a MongoDB field that will be used to store the account update key for each user on this cluster.
    clusters_valid.add_field("allocations", alloc_valid)
    # Hardware information
    clusters_valid.add_field("nbr_cpus", int, default=0)
    clusters_valid.add_field("nbr_gpus", int, default=0)
    # Links to the documentation
    clusters_valid.add_field("official_documentation", optional_string, default=False)
    clusters_valid.add_field("mila_documentation", optional_string, default=False)
    # Priority indice used to know in which order we display the clusters
    clusters_valid.add_field("display_order", int, default=9999)
    # Timezone of the cluster
    clusters_valid.add_field("timezone", timezone)

    # SSH connection and data fetching variables
    clusters_valid.add_field("remote_user", optional_string)
    clusters_valid.add_field("remote_hostname", optional_string)

    clusters_valid.add_field("ssh_key_filename", string)
    clusters_valid.add_field("ssh_port", integer)

    clusters_valid.add_field("sacct_path", optional_string)
    clusters_valid.add_field("sinfo_path", optional_string)

    # Load the clusters from the configuration file, asserting that it uses the
    # predefined format
    register_config("clusters", validator=clusters_valid)


def get_all_clusters():
    """
    List all the clusters.

    Returns:
        A list of the clusters' information
    """
    return get_config("clusters")


# Import the clusters from the config file
_load_clusters_from_config()
