
import base64
import random
import pytest

def get_random_string():
    b = str(random.random()).encode('utf-8')
    return base64.b64encode(b)

def test_get_nodes_list(mtclient, fake_data):
    LD_nodes = mtclient.nodes_list()

    assert len(LD_nodes) == len(fake_data['nodes'])

    S_names_A = set([D_node['name'] for D_node in LD_nodes])
    S_names_B = set([D_node['name'] for D_node in fake_data['nodes']])
    # S_names_B = set([
    #    'ci-computenode', 'cn-a001', 'cn-a002', 'cn-a003', 'cn-a004', 'cn-a005', 'cn-a006',
    #    'cn-a007', 'cn-a008', 'cn-a009', 'blg4101', 'blg4102', 'blg4103', 'blg4104', 'blg4105',
    #    'blg4106', 'blg4107', 'blg4108', 'blg4109', 'blg4110', 'gra1', 'gra2', 'gra3', 'gra4',
    #    'gra5', 'gra6', 'gra7', 'gra8', 'gra9', 'gra10', 'cdr2', 'cdr3', 'cdr4', 'cdr5', 'cdr6',
    #    'cdr25', 'cdr26', 'cdr27', 'cdr28', 'cdr29'])

    assert S_names_A == S_names_B


def test_unauthorized_get_nodes_list_00(unauthorized_mtclient_00):
    try:
        response = unauthorized_mtclient_00.nodes_list()
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)
#
def test_unauthorized_get_nodes_list_01(unauthorized_mtclient_01):
    try:
        response = unauthorized_mtclient_01.nodes_list()
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)

def test_unauthorized_get_nodes_one_00(unauthorized_mtclient_00):
    try:
        response = unauthorized_mtclient_00.nodes_one(name="doesntmatter")
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)
#
def test_unauthorized_get_nodes_one_01(unauthorized_mtclient_01):
    try:
        response = unauthorized_mtclient_01.nodes_one(name="doesntmatter")
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)


@pytest.mark.parametrize("cluster_name", ("mila", "cedar", "graham", "beluga", "sephiroth"))
def test_get_nodes_with_filter(mtclient, fake_data, cluster_name):
    """
    Analogous to the test in "clockwork_web_test/test_nodes.py" bearing the same name.
    """
    LD_nodes = mtclient.nodes_list(cluster_name=cluster_name)
    LD_original_nodes = [D_node for D_node in fake_data['nodes'] if D_node["cluster_name"] == cluster_name]

    assert len(LD_nodes) == len(LD_original_nodes), (
        "Lengths of lists don't match, so we shouldn't expect them to be able "
        "to match the elements themselves."
    )

    # agree on some ordering so you can zip the lists and have
    # matching elements in the same order
    LD_nodes = list(sorted(LD_nodes, key=lambda D_node: D_node['name']))
    LD_original_nodes = list(sorted(LD_original_nodes, key=lambda D_node: D_node['name']))

    # compare all the dicts one by one
    for (D_node, D_original_node) in zip(LD_nodes, LD_original_nodes):
        for k in D_original_node:
            assert D_node[k] == D_original_node[k]

    # S_names_A = set([D_node['name'] for D_node in LD_nodes])
    # S_names_B = set([D_node['name'] for D_node in fake_data['nodes'] if D_node["cluster_name"] == cluster_name])
    # assert S_names_A == S_names_B


@pytest.mark.parametrize("want_valid_name", (True, False))
@pytest.mark.parametrize("want_valid_cluster_name", (True, False, None))  # None for missing
def test_get_nodes_one(mtclient, fake_data, want_valid_name, want_valid_cluster_name):
    """
    Test many combinations of arguments for "nodes_one".
    Some leading to a successful query, some not.
    Since "cluster_name" is an optional argument, we can try with it
    and without it, and then try any variation of good and bad values.
    """

    assert fake_data['nodes']
    valid_D_node = random.choice(fake_data['nodes'])

    expected_match_to_be_found = True
    filter = {}
    if want_valid_name:
        filter["name"] = valid_D_node["name"]
    else:
        filter["name"] = get_random_string()
        expected_match_to_be_found = False
    #
    if want_valid_cluster_name == True:
        filter["cluster_name"] = valid_D_node["cluster_name"]
    elif want_valid_cluster_name is None:
        # we'll skip that argument so it doesn't influence
        # whether we'll find successfully or not
        pass
    else:
        filter["cluster_name"] = get_random_string()
        expected_match_to_be_found = False


    found_D_node = mtclient.nodes_one(**filter)
    if expected_match_to_be_found:
        for k in valid_D_node:
            assert valid_D_node[k] == found_D_node[k]
    else:
        # we expect an empty dict
        assert len(found_D_node) == 0
