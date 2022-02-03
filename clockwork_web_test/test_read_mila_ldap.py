from flask import current_app

import pytest
from clockwork_web.db import get_db, init_db
from clockwork_web.scripts import read_mila_ldap

import os
import tempfile
import json


def test_database_update_users(app):
    """
    This tests the connection to the database,
    but not the functionality of the web server.
    """

    LD_users = [
        {
            "mila_email_username": "johnsmith",
            "mila_cluster_username": "johnsmith",
            "mila_cluster_uid": "1500000001",
            "mila_cluster_gid": "1500000001",
            "display_name": "John Smith",
            "status": "enabled",
        },
        {
            "mila_email_username": "grouchomarx",
            "mila_cluster_username": "grouchomarx",
            "mila_cluster_uid": "1500000002",
            "mila_cluster_gid": "1500000002",
            "display_name": "Groucho Marx",
            "status": "disabled",
        },
    ]

    LD_users_updates = [
        {
            "mila_email_username": "johnsmith",
            "mila_cluster_username": "johnsmith",
            "mila_cluster_uid": "1500000001",
            "mila_cluster_gid": "1500000001",
            "display_name": "John Smith",
            "status": "disabled",  # this will change in the database
        },
        {
            "mila_email_username": "grouchomarx",
            "mila_cluster_username": "grouchomarx",
            "mila_cluster_uid": "1500000002",
            "mila_cluster_gid": "1500000002",
            "display_name": "Groucho Marx",
            # this should not be updated in the database even if it's
            # a different value
            "status": "enabled"  
        }
    ]

    # pick something unique that we don't care about
    collection_name = "users_test_9428384723"

    # Then verify that the contents is indeed there.
    # It should also contain some extra fields
    # such as "cc_account_username" which should be `None`.
    with app.app_context():

        mc = get_db()[current_app.config["MONGODB_DATABASE_NAME"]]
        mc[collection_name].delete_many({})

        ####
        ## The first part of the test is to populate the collection initially.
        ####

        read_mila_ldap.run(
            mongodb_connection_string=current_app.config["MONGODB_CONNECTION_STRING"],
            mongodb_database=current_app.config["MONGODB_DATABASE_NAME"],
            mongodb_collection=collection_name,
            LD_users=LD_users,
        )

        print(list(mc[collection_name].find()))

        for D_user in LD_users:

            LD_found_user = list(mc[collection_name].find(
                {"mila_email_username": D_user["mila_email_username"]}
            ))
            assert len(LD_found_user) == 1
            D_found_user = LD_found_user[0]
            for k in D_user:
                assert D_found_user[k] == D_user[k]
            assert D_found_user["cc_account_username"] is None
            assert D_found_user["status"] == D_user["status"]
            assert D_found_user["clockwork_api_key"] is None

        ####
        ## The second part of the test involves updating existing values.
        ####

        # Just set "cc_account_username" to anything so that we can make sure
        # that it wasn't accidentally set to `None` when performing the updates.
        for D_user in LD_users:
            mc[collection_name].update_one(
                {"mila_email_username": D_user["mila_email_username"]},
                {
                    "$set": {
                        "cc_account_username": ("cc_" + D_user["mila_email_username"]),
                        "clockwork_web_api": "0300whatever813817"
                    }
                })

        read_mila_ldap.run(
            mongodb_connection_string=current_app.config["MONGODB_CONNECTION_STRING"],
            mongodb_database=current_app.config["MONGODB_DATABASE_NAME"],
            mongodb_collection=collection_name,
            LD_users=LD_users_updates,
        )

        for D_user in LD_users_updates:
            D_found_user = mc[collection_name].find(
                {"mila_email_username": D_user["mila_email_username"]}
            )[0]
            for k in D_user:
                if k == "status":
                    # This is something specific that we test.
                    # They should both end up being "disabled".
                    assert D_found_user[k] == "disabled"
                elif k in ["cc_account_username", "clockwork_web_api"]:
                    assert D_found_user[k] is not None
                else:
                    assert D_found_user[k] == D_user[k]


        # clear out what you put in the db for this test
        mc[collection_name].delete_many({})

