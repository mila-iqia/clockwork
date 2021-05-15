
import numpy as np
import pyslurm
import re
from collections import defaultdict

LD_nodes = pyslurm.node().get().values()

def map_state_to_category(state):
    """
    This function looks a bit more complicated than it should because
    we have combined states like "DOWN*+DRAIN".
    I don't think we need to anticipate all combinations,
    but we'll be covered anyway.
    """

    # print(type(state), state)

    # Proceed by degree of seriousness in terms of what overrides what
    # for situations when we have "+" listed in the state.
    
    for s in ["RESERVED", "FUTURE"]:
        if s in state:
            # don't count those
            return None
    for s in ["DOWN", "DRAINED", "DRAINING", "FAIL", "FAILING", "MAINT", "REBOOT", "PERFCTRS", "POWER_DOWN", "POWERING_DOWN", "POWER_UP", "UNKNOWN"]:
        if s in state:
            return ("not_functional", "not_used")
    for s in ["MIXED", "ALLOCATED", "COMPLETING"]:
        if s in state:
            return ("functional", "used")
    if state in ["IDLE"]:
        return ("functional", "not_used")

    raise error(f"Encountered state that we never anticipated : {state}.")


D_res_counts = defaultdict(int)

for D_node in LD_nodes:
    # cpu=80,mem=386619M,billing=136,gres/gpu=8
    if m := re.match(r".*?gpu=(\d+).*?", D_node['tres_fmt_str']):
        nbr_gpus = int(m.group(1))
    else:
        # no gpus here; moving on
        continue
    
    state = D_node['state']
    c = map_state_to_category(state)
    if c is not None:
        D_res_counts[c] += nbr_gpus


for (k, v) in D_res_counts.items():
    print(f"In category {k} we have {v} gpus.")
