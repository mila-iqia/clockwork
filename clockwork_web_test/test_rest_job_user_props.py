import pytest
import base64


@pytest.fixture
def valid_rest_auth_headers_student00():
    """Fixture to be logged as student00"""
    email = "student00@mila.quebec"
    api_key = "000aaa00"
    s = f"{email}:{api_key}"
    encoded_bytes = base64.b64encode(s.encode("utf-8"))
    encoded_s = str(encoded_bytes, "utf-8")
    return {"Authorization": f"Basic {encoded_s}"}


def test_jobs_user_props_get(client, valid_rest_auth_headers_student00):
    job_id = "795002"
    cluster_name = "mila"
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"name": "je suis une user prop 1"}


def test_jobs_user_props_set(client, valid_rest_auth_headers_student00):
    job_id = "795002"
    cluster_name = "mila"
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "other value"},
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"name": "je suis une user prop 1", "other name": "other value"}

    # Back to default props
    client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": ["other name"]},
        headers=valid_rest_auth_headers_student00,
    )
    client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"name": "je suis une user prop 1"},
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    ).get_json() == {"name": "je suis une user prop 1"}


def test_jobs_user_props_delete(client, valid_rest_auth_headers_student00):
    # Set some props.
    job_id = "795002"
    cluster_name = "mila"
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "other value", "dino": "saurus"},
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {
        "name": "je suis une user prop 1",
        "other name": "other value",
        "dino": "saurus",
    }

    # Then delete some props.
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": ["name", "dino"]},
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    assert response.get_json() == ""

    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    )
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"other name": "other value"}

    # Back to default props
    client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": "other name"},
        headers=valid_rest_auth_headers_student00,
    )
    client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"name": "je suis une user prop 1"},
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    ).get_json() == {"name": "je suis une user prop 1"}


def test_size_limit_for_jobs_user_props_set(client, valid_rest_auth_headers_student00):
    job_id = "795002"
    cluster_name = "mila"
    huge_text = "x" * (2 * 1024 * 1024)
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": huge_text},
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 500
    assert response.get_json() == "Total props size limit exceeded (max. 2 Mbytes)."

    # Props should have not changed.
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    assert response.get_json() == {"name": "je suis une user prop 1"}
