"""
Test the node parser contained in slurm_state.sinfo_parser.
"""

from slurm_state.sinfo_parser import node_parser


def test_node_parser():
    # Open the file containing a fake sinfo report
    with open("slurm_state_test/files/sinfo_1", "r") as infile:
        nodes = list(node_parser(infile))

    # Define the node dictionary we are expecting to be
    # the output of the sinfo file's first node parsing
    node_0 = {
        "arch": "x86_64",
        "comment": "This is a comment",
        "cores": 2,
        "cpus": 2,
        "last_busy": 1681387881,
        "features": "test_features",
        "gres": "gpu:1",
        "gres_used": "gpu:0,tpu:0",
        "name": "test-node-1",
        "addr": "test-node-1",
        "state": "down",
        "state_flags": ["NOT_RESPONDING"],
        "memory": 1800,
        "reason": "Not responding",
        "reason_changed_at": 1667084449,
        "tres": "cpu=2,mem=1800M,billing=2",
        "tres_used": None,
    }

    # Check if the obtained result is the same as the expected one
    assert nodes[0] == node_0

    # Do a lighter check by only verifying the node ID of the second node
    assert nodes[1]["name"] == "test-node-2"
