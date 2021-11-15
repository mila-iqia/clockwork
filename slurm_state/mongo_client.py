from pymongo import MongoClient


def get_mongo_client(connection_string: str):
    """
    The first time calling this, you need to pass the proper connection string,
    but later on it's going to be filled in properly.

    Oftentimes the argument comes from
        connection_string = os.environ["MONGODB_CONNECTION_STRING"]

    Also, there is the tacit assumption that we're interested
    only in connecting to one database only so we can reuse clients.
    """
    if get_mongo_client.value is None:
        assert connection_string
        client = MongoClient(connection_string)
        get_mongo_client.value = client

    return get_mongo_client.value


get_mongo_client.value = None
