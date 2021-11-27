"""
These are additional filters that are to be applied to the
job entries of the form {"slurm" :..., "cw": ..., "user": ...}
of node entries of the form {"slurm" :..., "cw": ...}.

These can be a little messy, but they are meant to encapsulate
a collection of ugly hacks and manually-crafted tables.

This file requires the environment variable
slurm_state_ALLOCATIONS_RELATED_TO_MILA.
"""

import re
import os
import json
from collections import defaultdict

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


def extract_username_from_slurm_fields(D_slurm):
    """
    The exact user is not automatically included in the
    slurm fields (i.e. `D_job["slurm"]`).
    We need to infer it based on other fields.
    This involves a little bit of guesswork which is easy to do
    manually but can be automated by this function.

    This is not pretty, but at the moment we have to resort
    to approaches like this because our machine `blink` is
    not allowed to resolve usernames with the LDAP.
    The alternative is to manually build a table of correspondance
    with the UIDs, which is even messier.

    Since we are going to be matching a lot of variants of regex,
    we will give examples. Those examples will be anonymized
    to avoid mentioning specific users.
    """

    potential_guesses = []

    def f(D_slurm, k):
        # avoid problems with entries that are present but are `None`
        return str(D_slurm.get(k, ""))

    ### mila cluster ###

    # "command": "/home/mila/s/summbuf/
    # "work_dir": "/home/mila/s/summbuf/scripts/lol"
    # "std_err": "/home/mila/s/summbuf/randomsearch_90.log",
    # "std_in": "/dev/null",
    # "std_out": "/home/mila/s/summbuf/randomsearch_90.log",
    for k in ["command", "std_err", "std_in", "std_out", "work_dir"]:
        if m := re.match(r"/home/mila/[\.a-zA-Z0-9]{1}/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # "work_dir": "/home/mila/b/buffy.summers"
    if m := re.match(r"/home/mila/[a-zA-Z0-9]{1}/([^/]+)$", f(D_slurm, "work_dir")):
        potential_guesses.append(m.group(1))

    # !! This person has a dot in their username!?
    # "command": "/network/tmp1/buffy.summers/git/a/job.sh 0.1"
    for k in ["command", "work_dir"]:
        if m := re.match(r"/network/tmp\d/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # 'work_dir': '/network/tmp1/buffy.summers'
    for k in ["command", "work_dir"]:
        if m := re.match(r"/network/tmp\d/([^/]+)$", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # No idea what to do with that one. Is it a project?
    # 'work_dir': '/network/data2/tech-transfer/summbuf/some_project/neurips/bleh'
    # 'work_dir': '/network/data2/tech-transfer/summbuf/some_project'
    if m := re.match(
        r"/network/data\d/tech-transfer/([^/]+?)/.*", f(D_slurm, "work_dir")
    ):
        potential_guesses.append(m.group(1))
    # Let's pretend that we want to match "/network/data2/tech-transfer/summbuf" as well.
    if m := re.match(r"/network/data\d/tech-transfer/([^/]+)$", f(D_slurm, "work_dir")):
        potential_guesses.append(m.group(1))

    ### beluga ###

    # "work_dir": "/scratch/summbuf/log/data/treehouse"
    # "std_err": "/scratch/summbuf/log/data/treehouse/gamma-000.err",
    # "std_in": "/dev/null",
    # "std_out": "/scratch/summbuf/log/data/treehouse/gamma-000.out",

    for k in ["std_err", "std_in", "std_out", "work_dir"]:
        if m := re.match(r"/scratch/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # "std_err": "/lustre03/project/1111111/summbuf/treehouse/slurm-19741310.out",
    # "std_out": "/lustre03/project/1111111/summbuf/treehouse/slurm-19741310.out",
    # "work_dir": "/lustre03/project/1111111/summbuf/treehouse",
    for k in ["std_err", "std_in", "std_out", "work_dir"]:
        if m := re.match(r"/lustre\d+/project/\d+/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # Be careful with this one because there are cases when the command
    # comes from /home/mario-rrg

    # "command": "/home/summbuf/
    # "std_err": "/home/summbuf/treehouse/logs/allo.out",
    # "std_out": "/home/summbuf/treehouse/logs/allo.out",
    # "work_dir": "/home/summbuf/treehouse",
    for k in ["command", "std_err", "std_in", "std_out", "work_dir"]:
        if m := re.match(r"/home/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # "std_err": "/lustre04/scratch/summbuf/treehouse/separate_layers/allo/slurm-1111.out",
    # "std_out": "/lustre04/scratch/summbuf/treehouse/separate_layers/allo/slurm-1111.out",
    # "command": "/lustre04/scratch/summbuf/code/treehouse/scripts/train"
    for k in ["command", "std_err", "std_in", "std_out", "work_dir"]:
        if m := re.match(r"/lustre\d+/scratch/([^/]+?)/.*", f(D_slurm, k)):
            potential_guesses.append(m.group(1))

    # "work_dir": "/home/summbuf"
    if m := re.match(r"/home/([^/]+)$", f(D_slurm, "work_dir")):
        potential_guesses.append(m.group(1))

    # 'work_dir': '/lustre04/scratch/summbuf/allo'
    # 'work_dir': '/lustre04/scratch/summbuf/bye/src'
    if m := re.match(r"/lustre\d+/scratch/([^/]+?)/.*", f(D_slurm, "work_dir")):
        potential_guesses.append(m.group(1))

    # Some of the rules might lead to the user being guessed at "mila",
    # which is wrong in all cases. For example, this can happen for
    #     'work_dir': '/home/mila/s/summbuf/Github/allo'
    # and it's clearly not a good thing.
    # We will just remove those manually at this point.
    # Better to have "unknown" if nothing else could have been guessed
    # than to have "mila" pop up as user.
    potential_guesses = [e for e in potential_guesses if e != "mila"]

    # If we have a single guess, then declare it to be that.
    # Otherwise, vote.
    E = set(potential_guesses)
    if len(E) == 0:
        return "unknown"
    elif len(E) == 1:
        return potential_guesses[0]
    else:
        D = defaultdict(int)
        for guess in potential_guesses:
            D[guess] += 1

        # Vote.
        (max_guess, max_count) = sorted(D.items(), key=lambda e: e[1])[-1]
        return max_guess
