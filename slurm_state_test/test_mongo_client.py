import pytest
import os

from slurm_state.mongo_client import *


def test_get_mongo_client():
    val = get_mongo_client.value
    get_mongo_client.value = None
    try:
        conn = get_mongo_client(os.environ["MONGODB_CONNECTION_STRING"])
        # This is a bit of a hack ...
        assert type(conn).__name__ == "MongoClient"
        conn2 = get_mongo_client(None)
        assert conn is conn2
        conn.close()
    finally:
        get_mongo_client.value = val
