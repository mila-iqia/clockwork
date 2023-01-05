from base64 import b64encode

# We don't test the successful case here because it's tested in
# all the other tests.


def test_no_authentication(client):
    response = client.get("api/v1/clusters/jobs/list")
    assert response.status_code == 401
    assert "Authorization error" in response.get_data(as_text=True)


def test_bad_user(client):
    response = client.get(
        "api/v1/clusters/jobs/list",
        headers={
            "Authorization": f"Basic {b64encode(b'not_a_user:password').decode('ascii')}"
        },
    )
    assert response.status_code == 401
    assert "Authorization error" in response.get_data(as_text=True)


def test_bad_key(client, valid_rest_auth_headers):
    valid_rest_auth_headers["Authorization"] += "Mg=="
    response = client.get("api/v1/clusters/jobs/list", headers=valid_rest_auth_headers)
    assert response.status_code == 401
    assert "Authorization error" in response.get_data(as_text=True)
