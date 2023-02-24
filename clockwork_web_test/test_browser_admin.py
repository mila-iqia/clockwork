from flask import session
from flask_login import current_user
from flask_login import FlaskLoginClient
import pytest

from clockwork_web.db import get_db
from clockwork_web.user import User


@pytest.mark.parametrize(
    "admin_access,expected_return_code",
    (
        ("True", 200),
        ("true", 200),
        ("TRUE", 200),
        ("1", 200),
        (1, 200),
        (None, 403),
        ("", 403),
        ("false", 403),
        ("False", 403),
        ("tartiflette", 403),
        ("0", 403),
        (0, 403),
        (-1, 403),
    ),
)
def test_admin_panel(
    client, app, fake_data: dict[list[dict]], admin_access, expected_return_code
):
    """
    Checks that a user with admin rights has access to the admin page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """
    # Check that the fake_data provide users (otherwise, the tests are pointless)
    assert "users" in fake_data
    assert len(fake_data["users"]) > 0

    # Retrieve the name of an existing user from the fake_data
    user = fake_data["users"][0]
    user_id = user["mila_email_username"]

    # modify user entry in the database
    old_admin_access = user.get("admin_access", None)
    with app.app_context():
        users_collection = get_db()["users"]
        L = list(users_collection.find({"mila_email_username": user_id}))
        assert len(L) == 1
        users_collection.update_one(
            {"mila_email_username": user_id}, {"$set": {"admin_access": admin_access}}
        )

    login_response = client.get(f"/login/testing?user_id={user_id}")

    # Get the response
    response = client.get(f"/admin/panel")

    # restore user entry in the database
    with app.app_context():
        get_db()["users"].update_one(
            {"mila_email_username": user_id},
            {"$set": {"admin_access": old_admin_access}},
        )

    assert response.status_code == expected_return_code
