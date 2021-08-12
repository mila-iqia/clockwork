
# just a temporary test to make sure that the thing is wired properly
def test_wiring(mtclient):
    response = mtclient.jobs_list()
    assert response == "Success. Now put something real here.", response