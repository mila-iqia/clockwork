from urllib.parse import urlparse, parse_qs
from clockwork_web.login_routes import GOOGLE_DISCOVERY_URL


def fake_endpoints(mock, userinfo_text):
    mock.get(
        GOOGLE_DISCOVERY_URL,
        text="""{
        "authorization_endpoint": "https://localhost:8080/authorize",
        "token_endpoint": "https://localhost:8080/token",
        "userinfo_endpoint": "https://localhost:8080/userinfo"
        }""",
    )
    mock.register_uri(
        "POST",
        "https://localhost:8080/token",
        additional_matcher=lambda req: req.body
        == "grant_type=authorization_code&client_id=&code=patate32&redirect_uri=https%3A%2F%2Flocalhost%2Flogin%2Fcallback",
        text='{"access_token": "this_is_access_token"}',
    )
    mock.get(
        "https://localhost:8080/userinfo",
        request_headers={"Authorization": "Bearer this_is_access_token"},
        text=userinfo_text,
    )


def test_login(client_with_login, requests_mock):
    fake_endpoints(requests_mock, "")
    resp = client_with_login.get("/login/")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith(
        "https://localhost:8080/authorize?response_type=code&client_id=&redirect_uri=https%3A%2F%2Flocalhost%2Flogin%2Fcallback&scope=openid+email+profile&state="
    )


def test_login_noemail(client_with_login, requests_mock):
    fake_endpoints(requests_mock, "{}")
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"

    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert b"User email not available or not verified by Google." in resp.data


def test_login_nomila(client_with_login, requests_mock):
    fake_endpoints(
        requests_mock,
        '{"email_verified": true, "sub": 1234, "email": "random@gmail.com", "picture": "", "given_name": "Random"}',
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert b"We accept only accounts @mila.quebec" in resp.data


def test_login_new(client_with_login, requests_mock):
    fake_endpoints(
        requests_mock,
        '{"email_verified": true, "sub": "1234", "email": "user@mila.quebec", "picture": "", "given_name": "User"}',
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/"

    resp = client_with_login.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/jobs/"


def test_login_disabled(client_with_login, requests_mock):
    fake_endpoints(
        requests_mock,
        # This is synced with a "disabled" user in test_common/fake_data.json
        '{"email_verified": true, "sub": "4009", "email": "student09@mila.quebec", "picture": "", "given_name": "google_suite_user09"}',
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert resp.status_code == 200
    assert (
        b"The user retrieved does not have its status as &#39;enabled&#39;."
        in resp.data
    )


def test_logout(client_with_login, requests_mock):
    fake_endpoints(
        requests_mock,
        '{"email_verified": true, "sub": "1234", "email": "user@mila.quebec", "picture": "", "given_name": "User"}',
    )
    resp = client_with_login.get("/login/")
    res = urlparse(resp.headers["Location"])
    args = parse_qs(res.query)
    assert args["redirect_uri"][0] == "https://localhost/login/callback"
    code = "patate32"
    resp = client_with_login.get(
        "/login/callback", query_string=dict(code=code, state=args["state"][0])
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/"

    resp = client_with_login.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/jobs/"

    resp = client_with_login.get("/login/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://localhost/"

    resp = client_with_login.get("/")
    assert resp.status_code == 200
    assert b"Not logged in" in resp.data
