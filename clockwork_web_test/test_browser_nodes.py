"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr


The code for client.post(...) is from this amazing source:
    https://stackoverflow.com/questions/45703591/how-to-send-post-data-to-flask-using-pytest-flask


Lots of details about these tests depend on the particular values that we put in "fake_data.json".

"""

import json
import pytest


def test_nodes(client, fake_data: dict[list[dict]]):
    """
    Check that all the names of the nodes are present in the HTML generated.
    Note that the `client` fixture depends on other fixtures that
    are going to put the fake data in the database for us.
    """
    response = client.get("/nodes/list")
    for D_node in fake_data["nodes"]:
        assert D_node["name"].encode("utf-8") in response.data


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth")
)
def test_nodes_with_filter(client, fake_data: dict[list[dict]], cluster_name):
    """
    Same as `test_nodes` but adding a filter for the key "cluster_name".
    This tests the encoding of args with the ?k1=v1&k2=v2 notation in the url.
    """

    # Yes, "sephiroth" is a fake cluster name. There are no entries in the data for it.

    response = client.get(f"/nodes/list?cluster_name={cluster_name}")
    for D_node in fake_data["nodes"]:
        if D_node["cluster_name"] == cluster_name:
            assert D_node["name"].encode("utf-8") in response.data
        else:
            # We're being a little demanding here by asking that the name of the
            # host should never occur in the document. The host names are unique,
            # but there's no reason or guarantee that a string like "cn-a003" should NEVER
            # show up elsewhere in the page for some other reason.
            assert D_node["name"].encode("utf-8") not in response.data


# def test_single_job_missing_1111111(client):
#     """
#     This job entry should be missing from the database.
#     """
#     response = client.get("/jobs/single_job/1111111")
#     assert b"Found no job with job_id 1111111" in response.data
