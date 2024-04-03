import pytest
from clockwork_web.core.job_user_props_helper import (
    get_user_props,
    set_user_props,
    delete_user_props,
)


def test_get_user_props(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_student01(app, client):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    # Should return nothing because only student00 created props in fake data.
    with app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_unknown_cluster(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id = "795002"
        cluster_name = "unknown_cluster"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_unknown_job_id(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id = "999999"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_vs_fake_data(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        for fake_props_doc in fake_data["job_user_props"]:
            props = get_user_props(
                job_id=fake_props_doc["job_id"],
                cluster_name=fake_props_doc["cluster_name"],
            )
            assert fake_props_doc["props"] == props

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_set_user_props(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

        # Edit prop "name"
        assert (
            set_user_props(job_id, cluster_name, {"name": "new name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {"name": "new name"}
        )

        # Add prop "name2"
        assert (
            set_user_props(job_id, cluster_name, {"name2": "another name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {"name": "new name", "name2": "another name"}
        )

        # Add prop "my name is 3"
        assert (
            set_user_props(job_id, cluster_name, {"my name is 3": "third name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                "name": "new name",
                "name2": "another name",
                "my name is 3": "third name",
            }
        )

        # Edit props "name2" and "my name is 3"
        assert (
            set_user_props(
                job_id,
                cluster_name,
                {"my name is 3": "new third name", "name2": "new name 2"},
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                "name": "new name",
                "name2": "new name 2",
                "my name is 3": "new third name",
            }
        )

        # Edit prop "name" and add props "a", "bb" and "ccc".
        assert (
            set_user_props(
                job_id,
                cluster_name,
                {"a": 1, "bb": 2, "ccc": "hello", "name": "no name"},
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                "name": "no name",
                "name2": "new name 2",
                "my name is 3": "new third name",
                "a": 1,
                "bb": 2,
                "ccc": "hello",
            }
        )

        # Back to default props
        delete_user_props(
            job_id, cluster_name, ["name", "name2", "my name is 3", "a", "bb", "ccc"]
        )
        set_user_props(job_id, cluster_name, {"name": "je suis une user prop 1"})
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_set_user_props_limits(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Check default
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

        acceptable_field = "x" * (2 * 1024 * 512)

        # Should pass
        expected_props = {
            "name": "je suis une user prop 1",
            "huge field": acceptable_field,
        }
        assert (
            set_user_props(job_id, cluster_name, {"huge field": acceptable_field})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == expected_props
        )

        # Should fail
        very_huge_field = "x" * (2 * 1024 * 1024)
        with pytest.raises(ValueError, match="Too huge job-user props:"):
            set_user_props(job_id, cluster_name, {"huge field": very_huge_field})

        # Props should have not changed
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == expected_props
        )

        # Back to default props
        delete_user_props(job_id, cluster_name, ["huge field"])
        set_user_props(job_id, cluster_name, {"name": "je suis une user prop 1"})
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_delete_user_props(app, client):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Check default
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

        # Add props
        assert (
            set_user_props(
                job_id, cluster_name, {"a": 1, "bb": 2, "ccc": "hello", "d e f": "gg"}
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                "name": "je suis une user prop 1",
                "a": 1,
                "bb": 2,
                "ccc": "hello",
                "d e f": "gg",
            }
        )

        # Delete 1 prop by passing only a string
        delete_user_props(job_id, cluster_name, "bb")
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1",
            "a": 1,
            "ccc": "hello",
            "d e f": "gg",
        }

        # Pass a list of props to delete, with 1 valid prop and 1 non-existing prop.
        # Only valid prop should be deleted, the other should be ignored without error.
        delete_user_props(job_id, cluster_name, ["bb", "a"])
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1",
            "ccc": "hello",
            "d e f": "gg",
        }

        # Pass 2 valid props and 1 non-existing prop to delete.
        delete_user_props(
            job_id, cluster_name, ("ccc", "d e f", "unknown", "unknown prop")
        )
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

        # Pass 1 prop to delete as a list.
        # There should be no more props now.
        delete_user_props(job_id, cluster_name, ["name"])
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

        # Back to default props
        set_user_props(job_id, cluster_name, {"name": "je suis une user prop 1"})
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            "name": "je suis une user prop 1"
        }

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
