from pymongo import MongoClient


def get_mongo_client(config: dict = None):
    """
    The first time calling this, you need to pass the proper config,
    but later on it's going to be filled in properly.

    Also, there is the tacit assumption that we're interested
    only in connecting to one database only.
    """
    if get_mongo_client.value is None:
        assert config is not None
        for key in ["username", "password", "port", "hostname"]:
            assert key in config, "Missing %s in config : %s." % (key, str(config))

        if "connect_template" not in config:
            config[
                "connect_template"
            ] = "mongodb://<username>:<password>@<hostname>:<port>/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&ssl_cert_reqs=CERT_NONE&ssl=false"

        connection_string = (
            config["connect_template"]
            .replace("<username>", config["username"])
            .replace("<password>", config["password"])
            .replace("<hostname>", config["hostname"])
            .replace("<port>", str(config["port"]))
        )
        # print(connection_string)

        client = MongoClient(connection_string)
        get_mongo_client.value = client

    return get_mongo_client.value


get_mongo_client.value = None
