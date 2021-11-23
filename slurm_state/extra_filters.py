"""
These are additional filters that are to be applied to the
job entries of the form {"slurm" :..., "cw": ..., "user": ...}
of node entries of the form {"slurm" :..., "cw": ...}.

These can be a little messy, but they are meant to encapsulate
a collection of ugly hacks and manually-crafted tables.

This file requires the environment variable
slurm_state_ALLOCATIONS_RELATED_TO_MILA.
"""

import os
import json

assert os.environ.get(
    "slurm_state_ALLOCATIONS_RELATED_TO_MILA", ""
), "Missing the environment variable 'slurm_state_ALLOCATIONS_RELATED_TO_MILA'."
assert os.path.exists(os.environ["slurm_state_ALLOCATIONS_RELATED_TO_MILA"])


def is_allocation_related_to_mila(D_job: dict[dict]):
    """
    Usually used with a `filter` operation in order to let only
    the jobs that pertain to Mila, either because they are on our own
    Slurm cluster or because they are on allocations associated with us
    (as defined by the "mila_allocations_for_compute_canada.json" file).

    Return True when we want to keep the entry.
    """
    return (
        D_job["slurm"].get("account", "") in _get_mila_allocations_for_compute_canada()
    )


def _get_mila_allocations_for_compute_canada():
    if _get_mila_allocations_for_compute_canada.allocations is None:
        json_file = os.environ["slurm_state_ALLOCATIONS_RELATED_TO_MILA"]
        with open(json_file, "r") as f:
            E = json.load(f)
            return E
    else:
        return _get_mila_allocations_for_compute_canada.allocations


# a trick to load that file only once
_get_mila_allocations_for_compute_canada.allocations = None
