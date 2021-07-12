
"""
This seems like a good source of inspiration:
    https://medium.com/analytics-vidhya/how-to-test-flask-applications-aef12ae5181c

    https://github.com/pallets/flask/tree/1.1.2/examples/tutorial/flaskr
"""

import pytest

def test_create(client, user, app):
    
    print(client)
    print(user)

    with app.app_context():
        assert 2 == 2