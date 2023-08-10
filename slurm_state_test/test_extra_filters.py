import pytest

from slurm_state.extra_filters import (
    get_allocations,
)


@pytest.mark.parametrize(
    "cluster_name,expected_allocations",
    [
        ("mila", "*"),
        (
            "beluga",
            ["def-patate-rrg", "def-pomme-rrg", "def-cerise-rrg", "def-citron-rrg"],
        ),
    ],
)
def test_get_allocations(cluster_name, expected_allocations):
    """
    Tests the function get_allocations from the file slurm_state/extra_filters.py
    """
    assert get_allocations(cluster_name) == expected_allocations
