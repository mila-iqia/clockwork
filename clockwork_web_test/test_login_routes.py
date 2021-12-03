from urllib.parse import urlparse, parse_qs
from clockwork_web.login_routes import GOOGLE_DISCOVERY_URL


def test_login(client_with_login, requests_mock):
    requests_mock.get(
        GOOGLE_DISCOVERY_URL,
        text="""{
            "authorization_endpoint": "https://localhost:8080/authorize",
            "token_endpoint": "https://localhost:8080/token",
            "userinfo_endpoint": "https://localhost:8080/userinfo"
    }""",
    )
    resp = client_with_login.get("/login/")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith(
        "https://localhost:8080/authorize?response_type=code&client_id=None&redirect_uri=https%3A%2F%2Flocalhost%2Flogin%2Fcallback&scope=openid+email+profile&state="
    )


def test_login_noemail(client_with_login, requests_mock):
    requests_mock.get(
        GOOGLE_DISCOVERY_URL,
        text="""{
            "authorization_endpoint": "https://localhost:8080/authorize",
            "token_endpoint": "https://localhost:8080/token",
            "userinfo_endpoint": "https://localhost:8080/userinfo"
    }""",
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    # This fill fake the response from requests in the login code
    requests_mock.post(
        "https://localhost:8080/token", text='{"access_token": "this_is_access_token"}'
    )
    requests_mock.get("https://localhost:8080/userinfo", text="{}")

    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert b"User email not available or not verified by Google." in resp.data


def test_login_nomila(client_with_login, requests_mock):
    requests_mock.get(
        GOOGLE_DISCOVERY_URL,
        text="""{
            "authorization_endpoint": "https://localhost:8080/authorize",
            "token_endpoint": "https://localhost:8080/token",
            "userinfo_endpoint": "https://localhost:8080/userinfo"
    }""",
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    # This fill fake the response from requests in the login code
    requests_mock.post(
        "https://localhost:8080/token", text='{"access_token": "this_is_access_token"}'
    )
    requests_mock.get(
        "https://localhost:8080/userinfo",
        text='{"email_verified": true, "sub": 1234, "email": "random@gmail.com", "picture": "", "given_name": "Random"}',
    )

    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert b"We accept only accounts @mila.quebec" in resp.data


def Xtest_login_new(client_with_login, requests_mock):
    requests_mock.get(
        GOOGLE_DISCOVERY_URL,
        text="""{
            "authorization_endpoint": "https://localhost:8080/authorize",
            "token_endpoint": "https://localhost:8080/token",
            "userinfo_endpoint": "https://localhost:8080/userinfo"
    }""",
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    # This fill fake the response from requests in the login code
    requests_mock.post(
        "https://localhost:8080/token", text='{"access_token": "this_is_access_token"}'
    )
    requests_mock.get(
        "https://localhost:8080/userinfo",
        text='{"email_verified": true, "sub": 1234, "email": "user@mila.quebec", "picture": "", "given_name": "Random"}',
    )

    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/"

    resp = client_with_login.get("/")
    assert resp.status_code == 200
    assert "Not logged in" not in resp.data
