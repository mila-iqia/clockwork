"""
Helper function regarding the clusters.
"""
# Import the functions from clockwork_web.config
from clockwork_web.config import get_config, register_config

# Import the validators from clockwork_web.config
from clockwork_web.config import optional_string, SubdictValidator, string_list, string, timezone

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


def load_clusters_from_config():
    """
    Import the clusters from the config file
    """
    # Define the format of a cluster
    clusters_valid = SubdictValidator({})
    # Global information
    clusters_valid.add_field("organism", string)
    clusters_valid.add_field("timezone", timezone)
    # Allocations information
    clusters_valid.add_field("account_field", string)
    clusters_valid.add_field("allocations", alloc_valid)
    # Hardware information
    clusters_valid.add_field("nbr_cpus", int)
    clusters_valid.add_field("nbr_gpus", int)
    # Links to the documentation
    clusters_valid.add_field("official_documentation", string)
    clusters_valid.add_field("mila_documentation", optional_string)

    # Load the clusters from the configuration file, asserting that it uses the
    # predefined format
    register_config("clusters", validator=clusters_valid)


def get_all_clusters():
    """
    List all the clusters.

    Returns:
        A list of the clusters' information
    """
    return get_config('clusters')



# Import the clusters from the config file
load_clusters_from_config()
