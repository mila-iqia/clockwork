"""
Set of functions to test the API request regarding the GPUs
"""


def test_gpu_one_fail(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/gpu/one.

    No corresponding entry should be present in the database.
    """

    gpu_name = "rtx"
    response = client.get(
        f"/api/v1/clusters/gpu/one?gpu_name={gpu_name}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_result = response.json
    assert gpu_result == {}


def test_gpu_one_no_name(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/gpu/one.

    A 'Bad Request' code should be returned.
    """
    response = client.get("/api/v1/clusters/gpu/one", headers=valid_rest_auth_headers)
    assert response.status_code == 400


def test_gpu_one_success(client, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/gpu/one.

    Find a gpu entry that should be present in the database.
    """
    gpu_name = "rtx8000"
    response = client.get(
        f"/api/v1/clusters/gpu/one?gpu_name={gpu_name}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_result = response.json
    assert gpu_result == {
        "name": "rtx8000",
        "vendor": "nvidia",
        "ram": 48,
        "cuda_cores": 4608,
        "tensor_cores": 576,
        "tflops_fp32": 16.3,
    }


def test_gpu_list_success(client, fake_data, valid_rest_auth_headers):
    """
    Make a request to the REST API endpoint /api/v1/gpu/list.

    Find a list of gpu entries that should be present in the database.
    """
    # Create a dictionary of the gpus, omitting the "cw_name" of each entry
    expected_gpu_results = []
    for gpu_entry in fake_data["gpu"]:
        gpu_entry.pop("cw_name")
        expected_gpu_results.append(gpu_entry)

    response = client.get(
        f"/api/v1/clusters/gpu/list",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_results = response.json
    assert gpu_results == expected_gpu_results
