import random
import json
import pytest
import re
from clockwork_web.user import User


@pytest.mark.parametrize("route", ["/jobs/list", "/nodes/one"])
def test_presence_of_web_settings_javascript_variable(client, route, fake_data):
    """
    Check that the web_settings are present as a Javascript variable
    in all the routes. This should be automatic since they all inherit
    from base.html which defines that variable, but it's worth checking.
    Note that since we don't have the possibility of testing the Javascript
    code itself without modifying the routes served by the main application
    (which we might do later), we have to resort to looking up for the line
    where that "web_settings" variable is going to be found, and to validate
    that it indeed contains JSON that can be parsed.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
        nbr_items_per_page  The number of jobs we want to display per page
    """
    # Initialization
    assert len(fake_data["users"]) > 0
    current_user_id = fake_data["users"][0]["mila_email_username"]

    # Log in to Clockwork as this user
    login_response = client.get(f"/login/testing?user_id={current_user_id}")
    assert login_response.status_code == 302  # Redirect

    if route == "/nodes/one":
        node = fake_data["nodes"][0]["slurm"]
        full_route = (
            f"/nodes/one?node_name={node['name']}&cluster_name={node['cluster_name']}"
        )
    else:
        full_route = route

    response = client.get(full_route)
    assert response.status_code == 200

    body_text = response.get_data(as_text=True)

    # set `parsed_web_settings` to None so it will fail if the regex never matches any line
    parsed_web_settings = None
    for line in body_text.split("\n"):
        # This line should be present in the Javascript code.
        #     var web_settings = {% autoescape false %} JSON.parse('{{web_settings_json_str}}') {% endautoescape %}
        if m := re.match(r"^\s*var\sweb_settings.*JSON.parse\('(.*)'\).*?", line):
            # If we have a match, then m.group(1) should be the string that is to be parsed as JSON.
            try:
                parsed_web_settings = json.loads(m.group(1))
            except:
                assert (
                    False
                ), f"In route {route}, failed to parse the JSON string: {m.group(1)}\ncoming from the line : {line}"

    # Let's verify a few things about `parsed_web_settings` to make sure it contains valid values.
    # Tests run as the first user of the fake_data, so we can just compare against the default settings or something like that.
    user_web_settings = User.get(current_user_id).get_web_settings()

    assert parsed_web_settings == user_web_settings

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
