import json
import pytest


def test_000(client):
    """ """

    response = client.get("/")
    assert "clockwork" in response.get_data(as_text=True)
