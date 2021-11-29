"""

"""

from pprint import pprint
import random
import json
import pytest


@pytest.mark.parametrize("cluster_name", ("mila", "beluga", "cedar", "graham"))
def test_single_node_at_random(client, fake_data, valid_rest_auth_headers, cluster_name):
    """
    Make a request to the REST API endpoint /api/v1/clusters/nodes/one.

    Find a node entry that should be present in the database, for each cluster_name.
    """

    original_D_node = random.choice(
        [D_node for D_node in fake_data["nodes"] if D_node["slurm"]["cluster_name"] == cluster_name]
    )

    response = client.get(
        f"/api/v1/clusters/nodes/one?job_id={original_D_node['slurm']['name']}",
        headers=valid_rest_auth_headers,
    )
    assert "application/json" in response.content_type
    D_node = response.json

    for k1 in original_D_node:
        if k1 not in D_node:
            print(f"Missing key {k1} from fetched D_node.")
            pprint(original_D_node)
            pprint(D_node)        
        else:
            for k2 in original_D_node[k1]:
                if k2 not in D_node:
                    print(f"Missing key {k2} from fetched D_node[{k1}].")
                    pprint(original_D_node)
                    pprint(D_node)
                else:
                    assert D_node[k1][k2] == original_D_node[k1][k2], (k1, k2)


def test_single_node_missing(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/clusters/nodes/one.

    This node entry should be missing from the database.
    """

    # Make sure you pick a random `name` that's not in the database.
    S_node_names = set([D_node["slurm"]["name"] for D_node in fake_data["nodes"]])
    while True:
        node_name = "absent_node_%d" % int(random.random() * 1e7)
        if node_name not in S_node_names:
            break

    response = client.get(
        f"/api/v1/clusters/nodes/one?name={node_name}", headers=valid_rest_auth_headers
    )
    assert "application/json" in response.content_type
    D_node = response.json  # no `json()` here, just `json`
    assert D_node == {}


