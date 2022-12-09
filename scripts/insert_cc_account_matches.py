import os
import sys
import argparse
import json

from pymongo import MongoClient #, DeleteOne
# from pymongo.errors import BulkWriteError
from slurm_state.config import get_config


def main(argv):
    # Retrieve the args
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Adds to MongoDB all the CC associated accounts for the Mila accounts present.",
    )

    parser.add_argument(
        "-u",
        "--matches_path",
        help="JSON file where all the matches are stored.",
    )

    parser.add_argument(
        "--database_name", default="clockwork", help="Database name to inspect."
    )

    parser.add_argument(
        "--want_dry_run", action="store_true", help="Write out what you would do, but don't actually do it."
    )

    args = parser.parse_args(argv[1:])

    update_accounts(args.matches_path, args.database_name, args.want_dry_run)

def update_accounts(matches_path, database_name, want_dry_run):

    assert os.path.exists(matches_path)

    # indexed by username@mila.quebec, then contains three subdicts:
    #    "mila_ldap"
    #    "cc_roles"
    #    "cc_members"
    with open(matches_path) as f:
        DD_matches = json.load(f)

    if want_dry_run:
        client = None
    else:
        # Connect to MongoDB
        client = MongoClient(get_config("mongo.connection_string"))


    for mila_email_username, D_matches in DD_matches.items():

        if D_matches["cc_roles"] is not None:
            cc_account_username = D_matches["cc_roles"]["username"]
            if D_matches["cc_roles"]["status"].lower() == "activated":  # note the "status" key
                cc_account_status = "enabled"
            else:
                cc_account_status = "disabled"
            cc_account_ccri = D_matches["cc_roles"]["ccri"]
        elif D_matches["cc_members"] is not None:
            cc_account_username = D_matches["cc_members"]["username"]
            if D_matches["cc_members"]["activation_status"].lower() == "activated":  # note the "activation_status" key
                cc_account_status = "enabled"
            else:
                cc_account_status = "disabled"
            cc_account_ccri = D_matches["cc_members"]["ccri"]
        else:
            cc_account_username = None
            cc_account_status = None
            cc_account_ccri = None

        if cc_account_username is not None:
            if want_dry_run:
                print(f"Would update {mila_email_username} with {cc_account_username}")
            else:
                client[database_name]["users"].update_one(
                    {"mila_email_username": mila_email_username},
                    {"$set": {  "cc_account_username": cc_account_username,
                                "cc_account_status": cc_account_status,
                                "cc_account_ccri": cc_account_ccri}},
                    upsert=False)

if __name__ == "__main__":
    main(sys.argv)

"""
python3 scripts/insert_cc_account_matches.py --matches_path 2022-12-03_matches_done.json --want_dry_run

"""