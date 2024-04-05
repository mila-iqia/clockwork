import random
import pytest
import base64


def _get_test_user_props(fake_data):
    email = "student01@mila.quebec"
    # Find an entry that's associated with the user that's currently logged in.
    # This becomes the ground truth against which we compare the retrieved user props.
    LD_candidates = [
        D_job_user_props_entry
        for D_job_user_props_entry in fake_data["job_user_props"]
        if (
            D_job_user_props_entry["mila_email_username"] == email
            and len(D_job_user_props_entry["props"]) > 0
        )
    ]
    assert (
        len(LD_candidates) > 0
    ), "There should be at least one job_user_props entry for the user that's currently logged in."
    D_job_user_props_entry = random.choice(LD_candidates)

    job_id = D_job_user_props_entry["job_id"]
    cluster_name = D_job_user_props_entry["cluster_name"]
    original_props = D_job_user_props_entry["props"]
    return job_id, cluster_name, original_props


def test_jobs_user_props_get(client, valid_rest_auth_headers, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(fake_data)
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == original_props


def test_jobs_user_props_set(client, valid_rest_auth_headers, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(fake_data)
    assert "other name" not in original_props
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "other value"},
        },
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert len(props) == len(original_props) + 1
    assert props == {**original_props, "other name": "other value"}

    # Back to default props
    client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": ["other name"]},
        headers=valid_rest_auth_headers,
    )
    assert (
        client.get(
            f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
            headers=valid_rest_auth_headers,
        ).get_json()
        == original_props
    )


def test_jobs_user_props_delete(client, valid_rest_auth_headers, fake_data):
    # Set some props.
    job_id, cluster_name, original_props = _get_test_user_props(fake_data)
    assert "other name" not in original_props
    assert "dino" not in original_props
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "other value", "dino": "saurus"},
        },
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert len(props) == len(original_props) + 2
    assert props == {
        **original_props,
        "other name": "other value",
        "dino": "saurus",
    }

    # Then delete some props.
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": ["dino"]},
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    assert response.get_json() == ""

    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert response.status_code == 200
    props = response.get_json()
    assert len(props) == len(original_props) + 1
    assert props == {**original_props, "other name": "other value"}

    # Back to default props
    client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={"job_id": job_id, "cluster_name": cluster_name, "keys": "other name"},
        headers=valid_rest_auth_headers,
    )
    assert (
        client.get(
            f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
            headers=valid_rest_auth_headers,
        ).get_json()
        == original_props
    )


def test_size_limit_for_jobs_user_props_set(client, valid_rest_auth_headers, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(fake_data)
    assert "other  name" not in original_props
    huge_text = "x" * (2 * 1024 * 1024)
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": huge_text},
        },
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 500
    assert response.get_json() == "Total props size limit exceeded (max. 2 Mbytes)."

    # Props should have not changed.
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    assert response.get_json() == original_props
