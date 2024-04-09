import random
from clockwork_web.config import get_config


def _get_test_user_props(fake_data):
    email = get_config("clockwork.test.email")
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


def test_jobs_user_props_get_unknown_cluster(
    client, valid_rest_auth_headers, fake_data
):
    job_id, _, _ = _get_test_user_props(fake_data)
    cluster_name = "unknown_cluster"
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {}


def test_jobs_user_props_get_unknown_job_id(client, valid_rest_auth_headers, fake_data):
    _, cluster_name, _ = _get_test_user_props(fake_data)
    job_id = "unknown_job_id"
    response = client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {}


def test_jobs_user_props_set(client, valid_rest_auth_headers, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(fake_data)
    assert "other name" not in original_props
    assert "other name 2" not in original_props
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "other value", "other name 2": "other value 2"},
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
        "other name 2": "other value 2",
    }

    # Change value for existing prop 'other name`
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": {"other name": "new value for prop 'other name'"},
        },
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert len(props) == len(original_props) + 2
    assert props == {
        **original_props,
        "other name": "new value for prop 'other name'",
        "other name 2": "other value 2",
    }

    # Back to default props
    client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "keys": ["other name", "other name 2"],
        },
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
            "updates": {
                "other name": "other value",
                "dino": "saurus",
                "aa": "aa",
                "bb": "bb",
                "cc": "cc",
            },
        },
        headers=valid_rest_auth_headers,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert len(props) == len(original_props) + 5
    assert props == {
        **original_props,
        "other name": "other value",
        "dino": "saurus",
        "aa": "aa",
        "bb": "bb",
        "cc": "cc",
    }

    # Delete a prop with keys as a list of 1 string.
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "keys": ["dino"],
        },
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
    assert len(props) == len(original_props) + 4
    assert props == {
        **original_props,
        "other name": "other value",
        "aa": "aa",
        "bb": "bb",
        "cc": "cc",
    }

    # Delete some props with keys as a list of strings, including 1 unknown prop.
    response = client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        json={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "keys": ["aa", "bb", "unknown prop", "cc"],
        },
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
    # And delete a prop with keys as a string
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
