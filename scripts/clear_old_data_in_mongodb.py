"""
We have an incentive to periodically clear out the older data from the database.

We also want to migrate data locally to Atlas, and we want to be careful about

"""

from pymongo import MongoClient

# MONGODB_CONNECTION_STRING = 

deleted_count = MongoClient(MONGODB_CONNECTION_STRING)["clockwork"]["jobs"].delete_many({"command": "anonymized_for_fake_data"}).deleted_count
print(deleted_count)

deleted_count = MongoClient(MONGODB_CONNECTION_STRING)["clockwork"]["nodes"].delete_many({"os": "anonymized_for_fake_data"}).deleted_count
print(deleted_count)

deleted_count = MongoClient(MONGODB_CONNECTION_STRING)["clockwork"]["users"].delete_many({"clockwork_api_key": "000aaa"}).deleted_count
print(deleted_count)