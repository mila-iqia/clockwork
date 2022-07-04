"""
Tests fort the clockwork_web.core.clusters_helper functions.
"""

import pytest
from zoneinfo import ZoneInfo

from clockwork_web.core.clusters_helper import *


def test_get_all_clusters():
    """
    Test the function get_all_clusters.
    """
    D_expected_clusters = {
        "beluga": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": ZoneInfo(key="America/Montreal"),
            "account_field": "cc_account_username",
            "allocations": [
                "def-patate-rrg",
                "def-pomme-rrg",
                "def-cerise-rrg",
                "def-citron-rrg",
            ],
            "nbr_cpus": 1950,  # Number of CPUs on this cluster
            "nbr_gpus": 696,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.alliancecan.ca/wiki/B%C3%A9luga/",
            "mila_documentation": "https://docs.mila.quebec/Extra_compute.html#beluga",
        },
        "cedar": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": ZoneInfo(key="America/Vancouver"),
            "account_field": "cc_account_username",
            "allocations": [
                "def-patate-rrg",
                "def-pomme-rrg",
                "def-cerise-rrg",
                "def-citron-rrg",
            ],
            "nbr_cpus": 4948,  # Number of CPUs on this cluster
            "nbr_gpus": 1352,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.alliancecan.ca/wiki/Cedar",
            "mila_documentation": "https://docs.mila.quebec/Extra_compute.html#cedar",
        },
        "graham": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": ZoneInfo(key="America/Toronto"),
            "account_field": "cc_account_username",
            "allocations": [
                "def-patate-rrg",
                "def-pomme-rrg",
                "def-cerise-rrg",
                "def-citron-rrg",
            ],
            "nbr_cpus": 2660,  # Number of CPUs on this cluster
            "nbr_gpus": 536,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.alliancecan.ca/wiki/Graham",
            "mila_documentation": "https://docs.mila.quebec/Extra_compute.html#graham",
        },
        "mila": {
            "organism": "Mila",
            "timezone": ZoneInfo(key="America/Montreal"),
            "account_field": "mila_cluster_username",
            "allocations": "*",
            "nbr_cpus": 4860,  # Number of CPUs on this cluster
            "nbr_gpus": 532,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.mila.quebec/Information.html",
            "mila_documentation": False,
        },
        "narval": {
            "organism": "Digital Research Alliance of Canada",
            "timezone": ZoneInfo(key="America/Montreal"),
            "account_field": "cc_account_username",
            "allocations": [
                "def-patate-rrg",
                "def-pomme-rrg",
                "def-cerise-rrg",
                "def-citron-rrg",
            ],
            "nbr_cpus": 2608,  # Number of CPUs on this cluster
            "nbr_gpus": 636,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.alliancecan.ca/wiki/Narval",
            "mila_documentation": False,
        },
        "test_cluster": {
            "organism": "Mila",
            "timezone": ZoneInfo(key="America/Montreal"),
            "account_field": "test_cluster_username",
            "allocations": ["valid_fake_allocation_name", "clustergroup"],
            "nbr_cpus": 1,  # Number of CPUs on this cluster
            "nbr_gpus": -1,  # Number of GPUs on this cluster
            "official_documentation": "",
            "mila_documentation": False,
        },
    }

    assert D_expected_clusters == get_all_clusters()