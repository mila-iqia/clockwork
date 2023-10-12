"""Test status page."""

import re


def test_status_nb_users(client, fake_data):
    """
    Verify status page contains expected users count, i.e.
    number of users in database, number of enabled users,
    and number of users with a DRAC account.

    Parameters:
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """
    # Choose a user who have access to all the clusters
    user_dict = fake_data["users"][0]
    assert user_dict["mila_account_username"] is not None
    assert user_dict["cc_account_username"] is not None

    # Log in to Clockwork as this user
    login_response = client.get(
        f"/login/testing?user_id={user_dict['mila_email_username']}"
    )
    assert login_response.status_code == 302  # Redirect

    # Check users count in fake_data
    users = fake_data["users"]
    nb_users = len(users)
    nb_enabled_users = sum(
        (1 for user in users if user["status"] == "enabled"), start=0
    )
    nb_drac_users = sum(
        (1 for user in users if user.get("cc_account_username", None)), start=0
    )
    assert nb_users == 20
    assert nb_enabled_users == 18
    assert nb_drac_users == 19

    # Get status page content
    response = client.get("/status/")
    assert response.status_code == 200
    body_text = response.get_data(as_text=True)

    # Compile regex patterns to find users counts in page content
    re_nb_users = re.compile(
        r"<td>Number of users in database</td>\s+<td>([0-9]+)</td>"
    )
    re_nb_enabled_users = re.compile(
        r"<td>Number of enabled users</td>\s+<td>([0-9]+)</td>"
    )
    re_nb_drac_users = re.compile(
        r"<td>Number of users that have accounts matched to a DRAC account</td>\s+<td>([0-9]+)</td>"
    )

    # Search regex patterns
    result_nb_users = re_nb_users.search(body_text)
    result_nb_enabled_users = re_nb_enabled_users.search(body_text)
    result_nb_drac_users = re_nb_drac_users.search(body_text)

    # Check search results
    assert result_nb_users
    assert result_nb_enabled_users
    assert result_nb_drac_users
    # Each regex pattern must find user count in
    # first parenthesis content, stored in group(1).
    assert int(result_nb_users.group(1)) == nb_users
    assert int(result_nb_enabled_users.group(1)) == nb_enabled_users
    assert int(result_nb_drac_users.group(1)) == nb_drac_users
