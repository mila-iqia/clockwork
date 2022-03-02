"""
Set of functions to test the API request regarding hardware
"""


def test_hardware_gpu_one_fail(client, valid_rest_auth_headers):
    hardware_name = "rtx"
    response = client.get(
        f"/api/v1/clusters/hardware/gpu/one?gpu_name={hardware_name}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_result = response.json
    assert gpu_result == {}


def test_hardware_gpu_one_no_name(client, valid_rest_auth_headers):
    response = client.get(
        "/api/v1/clusters/hardware/gpu/one", headers=valid_rest_auth_headers
    )
    assert response.status_code == 400


def test_hardware_gpu_one_success(client, valid_rest_auth_headers):
    hardware_name = "rtx8000"
    response = client.get(
        f"/api/v1/clusters/hardware/gpu/one?gpu_name={hardware_name}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_result = response.json
    assert gpu_result == {
        "name": "rtx8000",
        "type": "gpu",
        "vendor": "nvidia",
        "ram": 48,
        "cuda_cores": 4608,
        "tensor_cores": 576,
        "tflops_fp32": 16.3,
    }


def test_hardware_gpu_list_success(client, valid_rest_auth_headers):
    response = client.get(
        f"/api/v1/clusters/hardware/gpu/list",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    gpu_results = response.json
    assert gpu_results == {
        "hardware_list": [
            {
                "name": "rtx8000",
                "type": "gpu",
                "vendor": "nvidia",
                "ram": 48,
                "cuda_cores": 4608,
                "tensor_cores": 576,
                "tflops_fp32": 16.3,
            },
            {
                "name": "v100",
                "type": "gpu",
                "vendor": "nvidia",
                "ram": 0,
                "cuda_cores": 5120,
                "tensor_cores": 640,
                "tflops_fp32": 0,
            },
            {
                "name": "a100",
                "type": "gpu",
                "vendor": "nvidia",
                "ram": 0,
                "cuda_cores": 0,
                "tensor_cores": 0,
                "tflops_fp32": 19.5,
            },
        ]
    }
