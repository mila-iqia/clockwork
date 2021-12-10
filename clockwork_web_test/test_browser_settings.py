from flask_login import current_user


def test_settings_index(client):
    response = client.get("/settings/")

    assert current_user.clockwork_api_key.encode("ascii") in response.data


def test_settings_new_key(client):
    # This is to establish a 'current_user'
    client.get("/settings/")

    api_key = current_user.clockwork_api_key

    response = client.get("/settings/new_key")

    assert current_user.clockwork_api_key != api_key

    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost/settings/"
