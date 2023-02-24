from flask import session
from flask_login import current_user
from flask_login import FlaskLoginClient
import pytest

from clockwork_web.db import get_db
from clockwork_web.user import User


def load_admin_page(client, fake_data: dict[list[dict]],  user_id):

    # # Check that the fake_data provide users (otherwise, the tests are pointless)
    # assert "users" in fake_data
    # assert len(fake_data["users"]) > 0

    # # Retrieve the name of an existing user from the fake_data
    # user = fake_data["users"][0]
    # user_id = user["mila_email_username"]

    # print(f"Using username {username}")

    # modify user entry in the database
    # old_admin_access = user.get("admin_access",None)
    # TODO
    # mc = get_db()
    # L = list(mc["users"].find({"mila_email_username": "student00@mila.quebec"}))
    # assert(len(L)==1)

    # print (L[0])

    login_response = client.get(f"/login/testing?user_id={user_id}")
    assert login_response.status_code == 302  # Redirect

    # Get the response
    response = client.get(f"/admin/panel")

    #restore user entry in the database
    # TODO

    return response


def test_admin_panel_user_admin(client, fake_data: dict[list[dict]]):
    """
    Checks that a user with admin rights has access to the admin page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """
    # Log in to Clockwork as the user student00@mila.quebec (admin)
    response = load_admin_page(client, fake_data, "student00@mila.quebec")
    assert response.status_code == 200

def test_admin_panel_user_not_admin(client, fake_data: dict[list[dict]]):
    """
    Checks that a user without admin rights does NOT have access to the admin page.

    Parameters
        client              The web client to request. Note that this fixture
                            depends on other fixtures that are going to put the
                            fake data in the database for us
        fake_data           The data our tests are based on
    """
    # Log in to Clockwork as the user student01@mila.quebec (NOT admin)
    response = load_admin_page(client, fake_data, "student01@mila.quebec")
    assert response.status_code == 403

