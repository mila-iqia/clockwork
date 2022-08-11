"""
Tests fort the clockwork_web.core.clusters_helper functions.
"""

import pytest

from clockwork_web.core.clusters_helper import *


def test_get_account_fields():
    """
    Test the function get_account_fields.
    """

    D_expected_account_fields = {
        "cc_account_username": ["beluga", "cedar", "graham", "narval"],
        "mila_cluster_username": ["mila"],
        "test_cluster_username": ["test_cluster"],
    }

    D_retrieved_account_fields = get_account_fields()
    assert D_expected_account_fields.keys() == D_retrieved_account_fields.keys()

    # Compare the list content
    for key in D_expected_account_fields.keys():
        assert set(D_expected_account_fields[key]) == set(
            D_retrieved_account_fields[key]
        )
