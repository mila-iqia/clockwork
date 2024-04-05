import pytest
import random
from clockwork_web.core.job_user_props_helper import (
    get_user_props,
    set_user_props,
    delete_user_props,
)


def _get_test_user_props(email, fake_data):
    # Find an entry that's associated with the user that's currently logged in.
    # This becomes the ground truth against which we compare the retrieved user props.
    LD_candidates = [
        D_job_user_props_entry
        for D_job_user_props_entry in fake_data["job_user_props"]
        if (
            D_job_user_props_entry["mila_email_username"] == email
            and len(D_job_user_props_entry["props"]) > 0
        )
    ]
    assert (
        len(LD_candidates) > 0
    ), "There should be at least one job_user_props entry for the user that's currently logged in."
    D_job_user_props_entry = random.choice(LD_candidates)

    job_id = D_job_user_props_entry["job_id"]
    cluster_name = D_job_user_props_entry["cluster_name"]
    original_props = D_job_user_props_entry["props"]
    return job_id, cluster_name, original_props


def test_get_user_props(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id, cluster_name, original_props = _get_test_user_props(
            mila_email_username, fake_data
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_student00(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student00@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    # We should not find any user props created by student00
    with pytest.raises(
        AssertionError,
        match=(
            "There should be at least one job_user_props entry "
            "for the user that's currently logged in."
        ),
    ):
        _get_test_user_props(mila_email_username, fake_data)

    # Should return nothing because only student01 created props in fake data.
    with app.app_context():
        # Get a user props dict from student01
        job_id, cluster_name, _ = _get_test_user_props(
            "student01@mila.quebec", fake_data
        )
        # Even using job_id and cluster_name, we should get nothing,
        # as current logged user is student00, not student01
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_unknown_cluster(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Get a valid job_id associated to a user prop dict
        job_id, _, _ = _get_test_user_props(mila_email_username, fake_data)
        # Use an unknown cluster name
        cluster_name = "unknown_cluster"
        # We should get nothing
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_get_user_props_from_unknown_job_id(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Get valid cluster name
        _, cluster_name, _ = _get_test_user_props(mila_email_username, fake_data)
        # Use an unknown job_id
        job_id = "999999"
        # We should get nothing
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {}

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_set_user_props(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        job_id, cluster_name, original_props = _get_test_user_props(
            mila_email_username, fake_data
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

        # Edit prop "name1"
        assert "name1" not in original_props
        assert (
            set_user_props(job_id, cluster_name, {"name1": "new name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {**original_props, "name1": "new name"}
        )

        # Add prop "my name 2"
        assert "my name 2" not in original_props
        assert (
            set_user_props(job_id, cluster_name, {"my name 2": "another name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {**original_props, "name1": "new name", "my name 2": "another name"}
        )

        # Add prop "my name is 3"
        assert "my name is 3" not in original_props
        assert (
            set_user_props(job_id, cluster_name, {"my name is 3": "third name"})
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                **original_props,
                "name1": "new name",
                "my name 2": "another name",
                "my name is 3": "third name",
            }
        )

        # Edit props "my name 2" and "my name is 3"
        assert (
            set_user_props(
                job_id,
                cluster_name,
                {"my name is 3": "new third name", "my name 2": "new name 2"},
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                **original_props,
                "name1": "new name",
                "my name 2": "new name 2",
                "my name is 3": "new third name",
            }
        )

        # Edit prop "name1" and add props "a", "bb" and "ccc".
        assert "a" not in original_props
        assert "bb" not in original_props
        assert "ccc" not in original_props
        assert (
            set_user_props(
                job_id,
                cluster_name,
                {"a": 1, "bb": 2, "ccc": "hello", "name1": "no name"},
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                **original_props,
                "name1": "no name",
                "my name 2": "new name 2",
                "my name is 3": "new third name",
                "a": 1,
                "bb": 2,
                "ccc": "hello",
            }
        )

        # Back to default props
        delete_user_props(
            job_id,
            cluster_name,
            ["name1", "my name 2", "my name is 3", "a", "bb", "ccc"],
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_set_user_props_limits(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Check default
        job_id, cluster_name, original_props = _get_test_user_props(
            mila_email_username, fake_data
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

        acceptable_field = "x" * (2 * 1024 * 512)

        # Should pass
        expected_props = {
            **original_props,
            "huge field": acceptable_field,
        }
        assert len(expected_props) == len(original_props) + 1
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
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect


def test_delete_user_props(app, client, fake_data):
    # Log in to Clockwork
    mila_email_username = "student01@mila.quebec"
    login_response = client.get(f"/login/testing?user_id={mila_email_username}")
    assert login_response.status_code == 302  # Redirect

    with app.app_context():
        # Check default
        job_id, cluster_name, original_props = _get_test_user_props(
            mila_email_username, fake_data
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

        # Add props
        assert (
            set_user_props(
                job_id, cluster_name, {"a": 1, "bb": 2, "ccc": "hello", "d e f": "gg"}
            )
            == get_user_props(job_id=job_id, cluster_name=cluster_name)
            == {
                **original_props,
                "a": 1,
                "bb": 2,
                "ccc": "hello",
                "d e f": "gg",
            }
        )

        # Delete 1 prop by passing only a string
        delete_user_props(job_id, cluster_name, "bb")
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            **original_props,
            "a": 1,
            "ccc": "hello",
            "d e f": "gg",
        }

        # Pass a list of props to delete, with 1 valid prop and 1 non-existing prop.
        # Only valid prop should be deleted, the other should be ignored without error.
        delete_user_props(job_id, cluster_name, ["bb", "a"])
        assert get_user_props(job_id=job_id, cluster_name=cluster_name) == {
            **original_props,
            "ccc": "hello",
            "d e f": "gg",
        }

        # Pass 2 valid props and 1 non-existing prop to delete.
        delete_user_props(
            job_id, cluster_name, ("ccc", "d e f", "unknown", "unknown prop")
        )
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

        # Pass 1 prop to delete as a list.
        one_prop_name = list(original_props.keys())[0]
        delete_user_props(job_id, cluster_name, [one_prop_name])
        expected_props = original_props.copy()
        del expected_props[one_prop_name]
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == expected_props
        )

        # Back to default props
        set_user_props(job_id, cluster_name, original_props)
        assert (
            get_user_props(job_id=job_id, cluster_name=cluster_name) == original_props
        )

    # Log out from Clockwork
    response_logout = client.get("/login/logout")
    assert response_logout.status_code == 302  # Redirect
