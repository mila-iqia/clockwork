
import json
import pytest

def test_000(client):
    """
    """

    response = client.get("/")
    assert b"clockwork" in response.data

