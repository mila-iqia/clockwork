from pprint import pprint
import random
import json
import pytest


@pytest.mark.parametrize("cluster_name", ("mila", "beluga", "cedar", "graham"))
def test_single_node_at_random(
    client, fake_data, valid_rest_auth_headers, cluster_name
):
    """
    Make a request to the REST API endpoint /api/v1/clusters/nodes/one.

    Find a node entry that should be present in the database, for each cluster_name.
    """

    original_D_node = random.choice(
        [
            D_node
            for D_node in fake_data["nodes"]
            if D_node["slurm"]["cluster_name"] == cluster_name
        ]
    )

    response = client.get(
        f"/api/v1/clusters/nodes/one?name={original_D_node['slurm']['name']}",
        headers=valid_rest_auth_headers,
    )
    assert response.status_code == 200
    assert "application/json" in response.content_type
    D_node = response.json

    assert original_D_node == D_node


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
    assert response.status_code == 200
    assert "application/json" in response.content_type
    D_node = response.json  # no `json()` here, just `json`
    assert D_node == {}


def test_node_list(client, valid_rest_auth_headers):
    response = client.get(
        f"/api/v1/clusters/nodes/list", headers=valid_rest_auth_headers
    )
    assert response.status_code == 200
    assert "application/json" in response.content_type


def test_single_node_gpu(client, fake_data, valid_rest_auth_headers):
    # Get if no parsed gpu
    response = client.get(
        f"/api/v1/clusters/nodes/one/gpu?name=ced0065", headers=valid_rest_auth_headers
    )
    assert response.status_code == 200
    assert "application/json" in response.content_type
    gpu_information = response.json
    assert gpu_information == {}

    # Get if a parsed gpu
    response = client.get(
        f"/api/v1/clusters/nodes/one/gpu?name=cn-c023", headers=valid_rest_auth_headers
    )
    assert response.status_code == 200
    assert "application/json" in response.content_type
    gpu_information = response.json
    assert gpu_information == {
        "name": "rtx8000",
        "vendor": "nvidia",
        "ram": 48,
        "cuda_cores": 4608,
        "tensor_cores": 576,
        "tflops_fp32": 16.3,
    }
