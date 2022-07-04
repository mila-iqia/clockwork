"""
Generates a json file with fake users to be used by
"anonymize_scontrol_report.py".

"""

import re
import os
import argparse
import json
import random

"""
    The "fake users" are going to have the following structure.
    [
        {
            "mila_email_username": "mario@mila.quebec",
            "status": "enabled",
            "clockwork_api_key": "000aaa"
            "cc_account_username": "ccuser040",
            "mila_cluster_username": milauser040",
            "cc_account_update_key": None
        },
        { ... },
        ...
    ]
"""


def get_predefined_fake_users(N=20):
    """
    Generate a complete description of users that
    we will add to our db["users"] collection.

    Every 10th user is going to have a disabled account
    because that's something that we'll want to test.

    Every 3rd user is going to present a personal picture.
    """

    L_cc_clusters = ["beluga", "graham", "cedar", "narval"]
    L_cc_accounts = [
        "def-patate-rrg",
        "def-pomme-rrg",
        "def-cerise-rrg",
        "def-citron-rrg",
    ]

    def gen_single_user(n):
        status = "disabled" if (n % 10 == 9) else "enabled"
        D_user = {
            "mila_email_username": "student%0.2d@mila.quebec" % n,
            "status": status,
            "clockwork_api_key": "000aaa%0.2d" % n,
            "mila_cluster_username": "milauser%0.2d" % n,
            "cc_account_username": "ccuser%0.2d" % n,
            "_extra": {
                "mila": {
                    "username": "milauser%0.2d" % n,
                    "uid": 10000 + n,
                    "account": "mila",
                    "cluster_name": "mila",
                }
            },
            "cc_account_update_key": None,
            "web_settings": {
                "nbr_items_per_page": 40,  # TODO: centralize this value
                "dark_mode": False,
            },
        }

        # then add the entries for all the clusters on CC
        account = L_cc_accounts[n % 2]
        for cluster_name in L_cc_clusters:
            D_user["_extra"][cluster_name] = {
                "username": "ccuser%0.2d" % n,
                "uid": 10000 + n,
                "account": account,
                "cluster_name": cluster_name,
            }

        # Add a link to a personal picture every 3rd user
        example_pictures = [
            "https://mila.quebec/wp-content/uploads/2019/08/guillaume_alain_400x700-400x400.jpg",
            "https://mila.quebec/wp-content/uploads/2016/03/moi-e1459380871782.jpg",
            "https://mila.quebec/wp-content/uploads/2021/12/20210704_143122-509x676.jpg"
        ] # Set of links to some sample pictures retrieved from the Mila website
        if (n % 3 == 0):
            D_user["personal_picture"] = example_pictures[random.randint(0, len(example_pictures)-1)]

        return D_user

    return [gen_single_user(n) for n in range(N)]


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Take a report from scontrol and strip out all identifying information.",
    )

    parser.add_argument("-o", "--output_file", help="Output file.")
    args = parser.parse_args(argv[1:])
    print(args)

    with open(args.output_file, "w") as f_out:
        LD_users = get_predefined_fake_users()
        json.dump(LD_users, f_out, indent=4)
        print(f"Wrote {args.output_file}.")


if __name__ == "__main__":
    import sys

    main(sys.argv)
