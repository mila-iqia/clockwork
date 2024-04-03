import pytest
import clockwork_tools.client
import os


@pytest.fixture
def client(config, db_with_fake_data):
    return clockwork_tools.client.ClockworkToolsClient(
        **{
            "host": os.environ["clockwork_tools_test_HOST"],
            "port": os.environ["clockwork_tools_test_PORT"],
            "email": "student00@mila.quebec",
            "clockwork_api_key": "000aaa00",
        }
    )


def test_cw_tools_get_user_props(client):
    job_id = "795002"
    cluster_name = "mila"
    props = client.get_user_props(job_id, cluster_name)
    assert props == {"name": "je suis une user prop 1"}


def test_cw_tools_set_user_props(client):
    job_id = "795002"
    cluster_name = "mila"
    props = client.set_user_props(job_id, cluster_name, {"a new name": "a new prop"})
    assert props == {"name": "je suis une user prop 1", "a new name": "a new prop"}


def test_cw_tools_delete_user_props(client):
    job_id = "795002"
    cluster_name = "mila"
    props = client.set_user_props(
        job_id,
        cluster_name,
        {"a new name": "a new prop", "aa": "aa", "bb": "bb", "cc": "cc"},
    )
    assert props == {
        "name": "je suis une user prop 1",
        "a new name": "a new prop",
        "aa": "aa",
        "bb": "bb",
        "cc": "cc",
    }

    assert client.delete_user_props(job_id, cluster_name, "name") == ""
    props = client.get_user_props(job_id, cluster_name)
    assert props == {"a new name": "a new prop", "aa": "aa", "bb": "bb", "cc": "cc"}

    assert client.delete_user_props(job_id, cluster_name, ["aa"]) == ""
    props = client.get_user_props(job_id, cluster_name)
    assert props == {"a new name": "a new prop", "bb": "bb", "cc": "cc"}

    assert client.delete_user_props(job_id, cluster_name, ["bb", "cc"]) == ""
    props = client.get_user_props(job_id, cluster_name)
    assert props == {"a new name": "a new prop"}
