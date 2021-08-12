
def test_get_nodes(mtclient):
    LD_nodes = mtclient.nodes_list()

    assert len(LD_nodes) == 40  # computed by hand with original file "fake_data.json"

    S_names_A = set([D_node['name'] for D_node in LD_nodes])
    S_names_B = set([
        'ci-computenode', 'cn-a001', 'cn-a002', 'cn-a003', 'cn-a004', 'cn-a005', 'cn-a006',
        'cn-a007', 'cn-a008', 'cn-a009', 'blg4101', 'blg4102', 'blg4103', 'blg4104', 'blg4105',
        'blg4106', 'blg4107', 'blg4108', 'blg4109', 'blg4110', 'gra1', 'gra2', 'gra3', 'gra4',
        'gra5', 'gra6', 'gra7', 'gra8', 'gra9', 'gra10', 'cdr2', 'cdr3', 'cdr4', 'cdr5', 'cdr6',
        'cdr25', 'cdr26', 'cdr27', 'cdr28', 'cdr29'])

    assert S_names_A == S_names_B


def test_unauthorized_get_nodes(unauthorized_mtclient_00):
    try:
        response = unauthorized_mtclient_00.nodes_list()
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)
        

def test_unauthorized_get_nodes(unauthorized_mtclient_01):
    try:
        response = unauthorized_mtclient_01.nodes_list()
    except Exception as e:
        assert "Server rejected call with code" in str(e)
        assert "Authorization error." in str(e)
