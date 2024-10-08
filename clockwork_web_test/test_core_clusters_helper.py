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
            "organization": "Digital Research Alliance of Canada",
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
            "official_documentation": "https://docs.alliancecan.ca/wiki/B%C3%A9luga",
            "mila_documentation": "https://docs.mila.quebec/Extra_compute.html#beluga",
            "display_order": 4,
            # "status": {
            #    "cluster_has_error": False,
            #    "jobs_are_old": True,
            # },
        },
        "cedar": {
            "organization": "Digital Research Alliance of Canada",
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
            "display_order": 3,
            # "status": {
            #    "cluster_has_error": False,
            #    "jobs_are_old": True,
            # },
        },
        "graham": {
            "organization": "Digital Research Alliance of Canada",
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
            "display_order": 5,
            # "status": {
            #    "cluster_has_error": False,
            #    "jobs_are_old": True,
            # },
        },
        "mila": {
            "organization": "Mila",
            "timezone": ZoneInfo(key="America/Montreal"),
            "account_field": "mila_cluster_username",
            "allocations": "*",
            "nbr_cpus": 4860,  # Number of CPUs on this cluster
            "nbr_gpus": 532,  # Number of GPUs on this cluster
            "official_documentation": "https://docs.mila.quebec/Information.html",
            "mila_documentation": False,
            "display_order": 1,
            # "status": {
            #    "cluster_has_error": False,
            #    "jobs_are_old": True,
            # },
        },
        "narval": {
            "organization": "Digital Research Alliance of Canada",
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
            "display_order": 2,
            # "status": {
            #    "cluster_has_error": False,
            #    "jobs_are_old": True,
            # },
        },
    }

    assert D_expected_clusters == get_all_clusters()


def test_get_account_fields():
    """
    Test the function get_account_fields.
    """
    expected_clusters_for_account_fields = {
        "cc_account_username": ["beluga", "cedar", "graham", "narval"],
        "mila_cluster_username": ["mila"],
    }

    retrieved_clusters_for_accound_fields = get_account_fields()

    for expected_account_field in expected_clusters_for_account_fields:
        assert expected_account_field in retrieved_clusters_for_accound_fields
        expected_clusters = expected_clusters_for_account_fields[expected_account_field]
        retrieved_clusters = retrieved_clusters_for_accound_fields[
            expected_account_field
        ]
        assert len(expected_clusters) == len(retrieved_clusters)
        assert set(expected_clusters) == set(retrieved_clusters)
