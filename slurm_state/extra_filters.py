"""
These are additional filters that are to be applied to the
job entries of the form {"slurm" :..., "cw": ..., "user": ...}
of node entries of the form {"slurm" :..., "cw": ...}.

These can be a little messy, but they are meant to encapsulate
a collection of ugly hacks and manually-crafted tables.
"""

import re
import os
import json
from collections import defaultdict
from .config import get_config, register_config, SubdictValidator, string_list

clusters_valid = SubdictValidator({})


def alloc_valid(value):
    if value == "*":
        return value
    return string_list(value)


clusters_valid.add_field("allocations", alloc_valid)

register_config("clusters", validator=clusters_valid)


def is_allocation_related_to_mila(D_job: dict[dict]):
    """
    Usually used with a `filter` operation in order to let only
    the jobs that pertain to Mila, either because they are on our own
    Slurm cluster or because they are on allocations associated with us.

    Returns True when we want to keep the entry.
    """
    cluster_name = D_job["slurm"]["cluster_name"]
    cluster_info = get_config("clusters").get(cluster_name, None)
    if cluster_info is None:
        return False
    allocations = cluster_info["allocations"]
    if allocations == "*":
        return True
    return D_job["slurm"].get("account", "") in allocations

def get_allocations(cluster_name):
    """
    Retrieve the allocations associated to a cluster from the 
    configuration file

    Parameter:
        cluster_name    The name of the cluster we want the allocations
                        associated to

    Returns:
        A list of strings (the names of the allocations), or "*" if set
        in the configuration file (it means "all the allocations of the cluster")
    """
    cluster_info = get_config("clusters").get(cluster_name, None)
    if cluster_info is None:
        return [] # We retrieve nothing
    return cluster_info["allocations"]