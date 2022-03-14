from pymongo import MongoClient
from .config import get_config, register_config

register_config("mongo.connection_string")
# This is not used here, but by clients
register_config("mongo.database_name", "clockwork")


def get_mongo_client():
    """
    Get a client for the configured database.
    """
    if get_mongo_client.value is None:
        client = MongoClient(get_config("mongo.connection_string"))
        get_mongo_client.value = client

    return get_mongo_client.value


get_mongo_client.value = None
