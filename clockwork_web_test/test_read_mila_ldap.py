from flask import current_app

import pytest
from clockwork_web.db import get_db, init_db
from clockwork_web.scripts import read_mila_ldap

import string
import random


def test_database_update_users(app):
    """
    This tests the connection to the database,
    but not the functionality of the web server.
    """

    LD_users = [
        {
            "mila_email_username": "johnsmith@mila.quebec",
            "mila_cluster_username": "johnsmith",
            "mila_cluster_uid": "1500000001",
            "mila_cluster_gid": "1500000001",
            "display_name": "John Smith",
            "status": "enabled",
        },
        {
            "mila_email_username": "grouchomarx@mila.quebec",
            "mila_cluster_username": "grouchomarx",
            "mila_cluster_uid": "1500000002",
            "mila_cluster_gid": "1500000002",
            "display_name": "Groucho Marx",
            "status": "disabled",
        },
    ]

    LD_users_updates = [
        {
            "mila_email_username": "johnsmith@mila.quebec",
            "mila_cluster_username": "johnsmith",
            "mila_cluster_uid": "1500000001",
            "mila_cluster_gid": "1500000001",
            "display_name": "John Smith",
            "status": "disabled",  # this will change in the database
        },
        {
            "mila_email_username": "grouchomarx@mila.quebec",
            "mila_cluster_username": "grouchomarx",
            "mila_cluster_uid": "1500000002",
            "mila_cluster_gid": "1500000002",
            "display_name": "Groucho Marx",
            # this should not be updated in the database even if it's
            # a different value
            "status": "enabled",
        },
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

        for D_user in LD_users:

            LD_found_user = list(
                mc[collection_name].find(
                    {"mila_email_username": D_user["mila_email_username"]}
                )
            )
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
                        "cc_account_username": (
                            "cc_" + D_user["mila_email_username"].split("@")[0]
                        ),
                        "clockwork_api_key": "0300whatever813817",
                    }
                },
            )

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
                elif k in ["cc_account_username", "clockwork_api_key"]:
                    assert D_found_user[k] is not None
                else:
                    assert D_found_user[k] == D_user[k]

        # clear out what you put in the db for this test
        mc[collection_name].delete_many({})


def test_client_side_user_updates():
    """
    This tests the function client_side_user_updates
    that has all the logic rules for the updates.
    This is indirectly tested also by `test_database_update_users`
    but we'll test it with more data here.
    """

    N = 100
    LD_users_DB = [
        {
            "mila_email_username": name + "@mila.quebec",
            "mila_cluster_username": name + "@mila.quebec",
            "mila_cluster_uid": "%d" % (1500000000 + i),
            "mila_cluster_gid": "%d" % (1500000000 + i),
            "display_name": name.upper(),  # whatever
            "status": "enabled" if random.random() > 0.5 else "disabled",
            "clockwork_api_key": None
            if random.random() > 0.5
            else str(random.random()),
            "cc_account_username": None if random.random() > 0.5 else ("cc_" + name),
        }
        for (i, name) in enumerate(
            "".join(
                random.choices(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits,
                    k=20,
                )
            )
            for _ in range(N)
        )
    ]

    LD_users_LDAP = []
    for D_user_DB in LD_users_DB:
        # copy it first
        D_user_LDAP = dict(e for e in D_user_DB.items())
        # those two fields will never be in LDAP updates
        del D_user_LDAP["clockwork_api_key"]
        del D_user_LDAP["cc_account_username"]
        D_user_LDAP["status"] = "enabled" if random.random() > 0.5 else "disabled"
        LD_users_LDAP.append(D_user_LDAP)

    # Then, because we want to have new users in the updates,
    # we'll just drop half of them from D_user_DB.
    random.shuffle(LD_users_DB)
    LD_users_DB = LD_users_DB[N // 2 :]

    LD_users_updated = read_mila_ldap.client_side_user_updates(
        LD_users_DB=LD_users_DB, LD_users_LDAP=LD_users_LDAP
    )

    # Again the trick to use dict to avoid N^2 perf.
    DD_users_DB = dict((e["mila_email_username"], e) for e in LD_users_DB)
    DD_users_LDAP = dict((e["mila_email_username"], e) for e in LD_users_LDAP)
    # Note that the whole point of testing is that we can express our success
    # conditions in a clearer/different way than the implementation.
    # If we just copy/pasted the cope from `client_side_user_updates` here
    # then we would hardly be testing its logic.

    for u in LD_users_updated:

        # Ask the question : Should u["status"] be "enabled"?
        answer = True

        # If it was present in the DB but wasn't enabled, the answer is False.
        if u["mila_email_username"] in DD_users_DB:
            if DD_users_DB[u["mila_email_username"]]["status"] != "enabled":
                answer = False

        # By construction we know that it's present in the LDAP, so now we check
        # to make sure it's enabled there too.
        answer = answer and (
            DD_users_LDAP[u["mila_email_username"]]["status"] == "enabled"
        )

        assert u["status"] == ("enabled" if answer else "disabled")


def test_process_user():
    source = {
        "attributes": {
            "apple-generateduid": ["AF54098F-29AE-990A-B1AC-F63F5A89B89"],
            "cn": ["john.smith", "John Smith"],
            "departmentNumber": [],
            "displayName": ["John Smith"],
            "employeeNumber": [],
            "employeeType": [],
            "gecos": [""],
            "gidNumber": ["1500000001"],
            "givenName": ["John"],
            "googleUid": ["john.smith"],
            "homeDirectory": ["/home/john.smith"],
            "loginShell": ["/bin/bash"],
            "mail": ["john.smith@mila.quebec"],
            "memberOf": [],
            "objectClass": [
                "top",
                "person",
                "organizationalPerson",
                "inetOrgPerson",
                "posixAccount",
            ],
            "physicalDeliveryOfficeName": [],
            "posixUid": ["smithj"],
            "sn": ["Smith"],
            "suspended": ["false"],
            "telephoneNumber": [],
            "title": [],
            "uid": ["john.smith"],
            "uidNumber": ["1500000001"],
        },
        "dn": "uid=john.smith,ou=IDT,ou=STAFF,ou=Users,dc=mila,dc=quebec",
    }

    target = {
        "mila_email_username": "john.smith@mila.quebec",
        "mila_cluster_username": "smithj",
        "mila_cluster_uid": "1500000001",
        "mila_cluster_gid": "1500000001",
        "display_name": "John Smith",
        "status": "enabled",
    }

    result = read_mila_ldap.process_user(source["attributes"])

    # make sure all the values match, and none have extra values
    for k in set(list(result.keys()) + list(target.keys())):
        assert result[k] == target[k]
