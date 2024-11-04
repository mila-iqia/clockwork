"""
Helper script to make sure testing db contains at least 1 admin user.
Used for frontend admin tests.
"""

from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config


def main():
    client = get_mongo_client()
    db = client[get_config("mongo.database_name")]
    users_collection = db["users"]
    users = sorted(
        users_collection.find({}), key=lambda user: user["mila_email_username"]
    )
    admin_users = [user for user in users if user.get("admin_access", False)]
    if not admin_users and users:
        future_admin_user = users[0]
        users_collection.update_one(
            {"mila_email_username": future_admin_user["mila_email_username"]},
            {"$set": {"admin_access": True}},
        )
        assert list(
            user
            for user in users_collection.find({})
            if user.get("admin_access", False)
        )
        print("Admin user registered.")


if __name__ == "__main__":
    main()
