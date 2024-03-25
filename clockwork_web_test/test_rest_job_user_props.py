import json

import pytest
from clockwork_web.server_app import create_app
from clockwork_web.db import get_db, init_db
from test_common.fake_data import populate_fake_data
import base64


@pytest.fixture(scope="function")
def local_client():
    """
    Create and configure a new client instance for each test.

    Inspired from `app` fixture, with scope set to "function" instead of "module",
    so that client is not shared across all tests. This is to make sure client is
    fully recreated in each test, thus modifications on database are
    entirely reset for each test. Doc:
    https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
    """

    app = create_app(
        extra_config={
            "TESTING": True,
            "LOGIN_DISABLED": True,
        }
    )
    with app.app_context():
        init_db()
        db = get_db()
        cleanup_function = populate_fake_data(db, mutate=True)

    with app.test_client() as client:
        # Yield client
        yield client

    cleanup_function()


@pytest.fixture
def valid_rest_auth_headers_student00():
    """Fixture to be logged as student00"""
    email = "student00@mila.quebec"
    api_key = "000aaa00"
    s = f"{email}:{api_key}"
    encoded_bytes = base64.b64encode(s.encode("utf-8"))
    encoded_s = str(encoded_bytes, "utf-8")
    return {"Authorization": f"Basic {encoded_s}"}


def test_jobs_user_props_get(local_client, valid_rest_auth_headers_student00):
    job_id = 795002
    cluster_name = "mila"
    response = local_client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"name": "je suis une user prop 1"}


def test_jobs_user_props_set(local_client, valid_rest_auth_headers_student00):
    job_id = 795002
    cluster_name = "mila"
    response = local_client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        data={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": json.dumps({"other name": "other value"}),
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"name": "je suis une user prop 1", "other name": "other value"}


def test_jobs_user_props_delete(local_client, valid_rest_auth_headers_student00):
    # Set some props.
    job_id = 795002
    cluster_name = "mila"
    response = local_client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        data={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": json.dumps({"other name": "other value", "dino": "saurus"}),
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
    response = local_client.put(
        f"/api/v1/clusters/jobs/user_props/delete",
        data={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "keys": json.dumps(["name", "dino"]),
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    props = response.get_json()
    assert props == {"other name": "other value"}


def test_size_limit_for_jobs_user_props_set(
    local_client, valid_rest_auth_headers_student00
):
    job_id = 795002
    cluster_name = "mila"
    huge_text = "x" * (2 * 1024 * 1024)
    response = local_client.put(
        f"/api/v1/clusters/jobs/user_props/set",
        data={
            "job_id": job_id,
            "cluster_name": cluster_name,
            "updates": json.dumps({"other name": huge_text}),
        },
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 500
    assert response.get_json().startswith("Too huge job-user props: ")

    # Props should have not changed.
    response = local_client.get(
        f"/api/v1/clusters/jobs/user_props/get?cluster_name={cluster_name}&job_id={job_id}",
        headers=valid_rest_auth_headers_student00,
    )
    assert response.content_type == "application/json"
    assert response.status_code == 200
    assert response.get_json() == {"name": "je suis une user prop 1"}
