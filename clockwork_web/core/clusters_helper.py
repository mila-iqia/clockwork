"""
Helper function regarding the clusters.
"""
# Import the functions from clockwork_web.config
from clockwork_web.config import get_config, register_config

# Import the validators from clockwork_web.config
from clockwork_web.config import (
    optional_string,
    SubdictValidator,
    string_list,
    string,
    timezone,
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
    clusters_valid.add_field("organism", optional_string, default=False)
    clusters_valid.add_field("timezone", timezone)
    # Allocations information
    clusters_valid.add_field("account_field", string)
    clusters_valid.add_field("allocations", alloc_valid)
    # Hardware information
    clusters_valid.add_field("nbr_cpus", int, default=0)
    clusters_valid.add_field("nbr_gpus", int, default=0)
    # Links to the documentation
    clusters_valid.add_field("official_documentation", optional_string, default=False)
    clusters_valid.add_field("mila_documentation", optional_string, default=False)

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


def get_account_fields():
    """
    Retrieve the keys identifying the account for each cluster. Follows an
    example of the returned dictionary:
    {
        "cc_account_username": ["beluga", "cedar", "graham", "narval"],
        "mila_cluster_username": ["mila"],
        "test_cluster_username": ["test_cluster"]
    }
    """
    # Retrieve the information on the clusters
    D_all_clusters = get_all_clusters()

    # Initialize the dictionary of account fields
    D_account_fields = {}

    for cluster_name in D_all_clusters.keys():
        # For each cluster, get the name of the account field
        account_field = D_all_clusters[cluster_name]["account_field"]

        # If the account field is known in D_account_fields, add the name of the
        # cluster in the associated clusters array
        # Otherwise, associate a list containing the current cluster's name
        # to the account field
        D_account_fields.setdefault(account_field, []).append(cluster_name)

    # Return the dictionary presenting the different account fields and their
    # associated clusters
    return D_account_fields
