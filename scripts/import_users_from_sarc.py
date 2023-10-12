"""

"""

import argparse
import json
from pymongo import MongoClient, UpdateOne


def process_user(D_sarc_user):
    """
    Convert a dictionary describing a user from the format used by SARC to the format
    used by Clockwork.

    Parameter:
        D_sarc_user     A dictionary describing a user in the format used by SARC

    Returns:
        A dictionary describing a user in the format used by Clockwork
    """
    user = {
        "mila_email_username": D_sarc_user["mila"]["email"],
        "display_name": D_sarc_user["mila_ldap"]["display_name"],
        "mila_account_username": D_sarc_user["mila_ldap"]["mila_account_username"],
        "mila_cluster_uid": D_sarc_user["mila_ldap"]["mila_cluster_uid"],
        "mila_cluster_gid": D_sarc_user["mila_ldap"]["mila_cluster_gid"],
        "status": "enabled" if D_sarc_user["mila"]["active"] else "disabled",
        "cc_account_username": D_sarc_user["drac_members"]["username"]
        if D_sarc_user["drac_members"] is not None
        else None,
        "cc_account_ccri": D_sarc_user["drac_members"]["ccri"]
        if D_sarc_user["drac_members"] is not None
        else None,
    }
    return user


def client_side_user_updates(LD_users_DB, LD_users_LDAP):
    """
    Instead of having complicated updates that depend on multiple MongoDB
    updates to cover all cases involving the "status" field, we'll do all
    that logic locally in this function.

    We have `LD_users_DB` from our database, we have `LD_users_LDAP` from
    our LDAP server, and then we return list of updates to be commited.

    Note that both `LD_users_DB` and `LD_users_LDAP` use the same fields.
    """
    # The first step is to index everything by unique id, which is
    # the "mila_email_username". This is because we'll be matching
    # entries from both lists and we want to avoid N^2 performance.

    DD_users_DB = dict((e["mila_email_username"], e) for e in LD_users_DB)
    DD_users_LDAP = dict((e["mila_email_username"], e) for e in LD_users_LDAP)

    LD_users_to_update_or_insert = []
    for meu in set(list(DD_users_DB.keys()) + list(DD_users_LDAP.keys())):
        # `meu` is short for the mila_email_username value

        if meu in DD_users_DB and not meu in DD_users_LDAP:
            # User is in DB but not in the LDAP. Don't change it in DB.
            # Don't even update it. This situation is an exception
            # what might happen for special admin accounts or something,
            # but never with regular student accounts.
            continue
        elif meu not in DD_users_DB and meu in DD_users_LDAP:
            # User is not in DB but is in the LDAP. That's a new entry!
            # We want to dress it up and commit it to the DB.
            entry = DD_users_LDAP[meu]
            # entry["cc_account_username"] = None
            entry["clockwork_api_key"] = None
            entry["cc_account_update_key"] = None
            # Any web_settings not present will pull values
            # from `get_default_web_settings_values()` later down
            # the road. It would actually be better to leave them out
            # at this point and not fill them with anything hardcoded.
            # Just make sure you make this a dict, though.
            entry["web_settings"] = {}
            assert "status" in entry  # sanity check
        else:
            # User is in DB and in LDAP. Update it carefully and don't
            # disturb the fields that shouldn't be touched.
            entry = DD_users_DB[meu]
            if DD_users_LDAP[meu]["status"] == "disabled":
                # No matter what we said in the database, if the LDAP
                # says that it's disabled, then we propagate that change.
                # We wouldn't do the same thing with "enabled" in the LDAP, though.
                entry["status"] = "disabled"
            assert "cc_account_username" in entry  # sanity check
            assert "clockwork_api_key" in entry  # sanity check

        LD_users_to_update_or_insert.append(entry)
    return LD_users_to_update_or_insert


if __name__ == "__main__":

    # Retrieve the arguments
    parser = argparse.ArgumentParser(
        description="Update the MongoDB database users based on values returned from a JSON file listing the users and retrieved from SARC."
    )

    parser.add_argument(
        "--mongodb_connection_string",
        default=None,
        type=str,
        help="(optional) MongoDB connection string. Contains username and password.",
    )

    parser.add_argument(
        "--mongodb_database",
        default="clockwork",
        type=str,
        help="(optional) MongoDB database to modify. Better left at default.",
    )
    parser.add_argument(
        "--mongodb_collection",
        default="users",
        type=str,
        help="(optional) MongoDB collection to modify. Better left at default.",
    )
    parser.add_argument(
        "--input_json_file",
        default=None,
        type=str,
        help="(optional) Ignore the LDAP and load from this json file instead.",
    )

    args = parser.parse_args()

    # Retrieve users from the input file
    with open(args.input_json_file, "r") as infile:
        LD_sarc_users = json.load(infile)

    # Process them in order to keep only information used in Clockwork
    LD_users = [process_user(D_sarc_user) for D_sarc_user in LD_sarc_users]

    # Update the users collection in the database
    if (
        args.mongodb_connection_string
        and args.mongodb_database
        and args.mongodb_collection
    ):
        # Define the collection of the database on which we work
        users_collection = MongoClient(args.mongodb_connection_string)[
            args.mongodb_database
        ][args.mongodb_collection]
        # List all the users already contained in this collection
        LD_users_DB = list(users_collection.find())

        L_updated_users = client_side_user_updates(
            LD_users_DB=LD_users_DB, LD_users_LDAP=LD_users
        )

        L_updates_to_do = [
            UpdateOne(
                {"mila_email_username": updated_user["mila_email_username"]},
                {
                    # We set all the fields corresponding to the fields from `updated_user`,
                    # so that's a convenient way to do it. Note that this does not affect
                    # the fields in the database that are already present for that user.
                    "$set": updated_user,
                },
                upsert=True,
            )
            for updated_user in L_updated_users
        ]

        if L_updates_to_do:
            result = users_collection.bulk_write(
                L_updates_to_do
            )  #  <- the actual commit
