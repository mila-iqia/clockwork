import pytest
from clockwork_web.core.job_user_props_helper import (
    get_user_props,
    set_user_props,
    delete_user_props,
)
from clockwork_web.server_app import create_app
from clockwork_web.db import get_db, init_db
from test_common.fake_data import populate_fake_data


@pytest.fixture(scope="function")
def local_logged_app(request):
    """
    Create and configure a new app instance for each test.

    Inspired from `app` fixture, with changes:

    - Scope is "function" instead of "module", so that app is not shared across
      all tests. This is to make sure app is fully recreated in each test, thus
      modifications on database are entirely reset for each test. Doc:
      https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session

    - User is automatically logged (using app.test_client()) with student00 by default.

    - When using this fixture in a test, we can change logged user by marking test with
      `@pytest.mark.mila_email_username("your-user-here@mila.quebec"). Given username
      will then be used instead of "student00@mila.quebec". Doc:
      https://docs.pytest.org/en/6.2.x/fixture.html#using-markers-to-pass-data-to-fixtures
    """

    # Retrieve username to log in.
    marker = request.node.get_closest_marker("mila_email_username")
    if marker is None:
        mila_email_username = "student00@mila.quebec"
    else:
        mila_email_username = marker.args[0]

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
        # Log in to Clockwork
        login_response = client.get(f"/login/testing?user_id={mila_email_username}")
        assert login_response.status_code == 302  # Redirect

        # Yield app
        yield app

        # Log out from Clockwork
        response_logout = client.get("/login/logout")
        assert response_logout.status_code == 302  # Redirect

    cleanup_function()


def test_get_user_props(local_logged_app):
    with local_logged_app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1"}


@pytest.mark.mila_email_username("student01@mila.quebec")
def test_get_user_props_from_student01(local_logged_app):
    # Should fail because only student00 created props in fake data.
    with local_logged_app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == {}
        )


def test_get_user_props_from_unknown_cluster(local_logged_app):
    with local_logged_app.app_context():
        job_id = "795002"
        cluster_name = "unknown_cluster"
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == {}
        )


def test_get_user_props_from_unknown_job_id(local_logged_app):
    with local_logged_app.app_context():
        job_id = "999999"
        cluster_name = "mila"
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == {}
        )


def test_get_user_props_vs_fake_data(local_logged_app, fake_data):
    with local_logged_app.app_context():
        for fake_props_doc in fake_data["job_user_props"]:
            props = get_user_props(
                job_id=fake_props_doc["job_id"],
                cluster_name=fake_props_doc["cluster_name"],
            )
            assert fake_props_doc["props"] == props


def test_set_user_props(local_logged_app):
    with local_logged_app.app_context():
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1"}

        # Edit prop "name"
        set_user_props(job_id, cluster_name, {"name": "new name"})
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "new name"}

        # Add prop "name2"
        set_user_props(job_id, cluster_name, {"name2": "another name"})
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "new name", "name2": "another name"}

        # Add prop "my name is 3"
        set_user_props(job_id, cluster_name, {"my name is 3": "third name"})
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "new name", "name2": "another name", "my name is 3": "third name"}

        # Edit props "name2" and "my name is 3"
        set_user_props(
            job_id,
            cluster_name,
            {"my name is 3": "new third name", "name2": "new name 2"},
        )
        assert get_user_props(job_id=job_id, cluster_name=cluster_name,) == {
            "name": "new name",
            "name2": "new name 2",
            "my name is 3": "new third name",
        }

        # Edit prop "name" and add props "a", "bb" and "ccc".
        set_user_props(
            job_id, cluster_name, {"a": 1, "bb": 2, "ccc": "hello", "name": "no name"}
        )
        assert get_user_props(job_id=job_id, cluster_name=cluster_name,) == {
            "name": "no name",
            "name2": "new name 2",
            "my name is 3": "new third name",
            "a": 1,
            "bb": 2,
            "ccc": "hello",
        }


def test_set_user_props_limits(local_logged_app):
    with local_logged_app.app_context():
        # Check default
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1"}

        acceptable_field = "x" * (2 * 1024 * 512)

        # Should pass
        set_user_props(job_id, cluster_name, {"huge field": acceptable_field})
        expected_props = {
            "name": "je suis une user prop 1",
            "huge field": acceptable_field,
        }
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == expected_props
        )

        # Should fail
        very_huge_field = "x" * (2 * 1024 * 1024)
        with pytest.raises(ValueError, match="Too huge job-user props:"):
            set_user_props(job_id, cluster_name, {"huge field": very_huge_field})

        # Props should have not changed
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == expected_props
        )


def test_delete_user_props(local_logged_app):
    with local_logged_app.app_context():
        # Check default
        job_id = "795002"
        cluster_name = "mila"
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1"}

        # Add props
        set_user_props(
            job_id, cluster_name, {"a": 1, "bb": 2, "ccc": "hello", "d e f": "gg"}
        )
        assert get_user_props(job_id=job_id, cluster_name=cluster_name,) == {
            "name": "je suis une user prop 1",
            "a": 1,
            "bb": 2,
            "ccc": "hello",
            "d e f": "gg",
        }

        # Delete 1 prop by passing only a string
        delete_user_props(job_id, cluster_name, "bb")
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1", "a": 1, "ccc": "hello", "d e f": "gg"}

        # Pass a list of props to delete, with 1 valid prop and 1 non-existing prop.
        # Only valid prop should be deleted, the other should be ignored without error.
        delete_user_props(job_id, cluster_name, ["bb", "a"])
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1", "ccc": "hello", "d e f": "gg"}

        # Pass 2 valid props and 1 non-existing prop to delete.
        delete_user_props(
            job_id, cluster_name, ("ccc", "d e f", "unknown", "unknown prop")
        )
        assert get_user_props(
            job_id=job_id,
            cluster_name=cluster_name,
        ) == {"name": "je suis une user prop 1"}

        # Pass 1 prop to delete as a list.
        # There should be no more props now.
        delete_user_props(job_id, cluster_name, ["name"])
        assert (
            get_user_props(
                job_id=job_id,
                cluster_name=cluster_name,
            )
            == {}
        )
