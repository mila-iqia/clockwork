"""
Generates a json file with fake users to be used by
"anonymize_scontrol_report.py".

"""

import re
import os
import argparse
import json

"""
    The "fake users" are going to have the following structure.
    The "accounts_on_clusters" might have to be revised if it
    leads to awkward/suboptimal requests for MongoDB.
    [
        {
            "google_suite": {   "id": "009643",
                                "name": "mario",
                                "email": "mario@mila.quebec",
                                "profile_pic": ""},
            "cw": { "status": "enabled",
                    "clockwork_api_key": "000aaa"},
            {"accounts_on_clusters":
                {
                    "beluga":
                        {
                            "username": "ccuser040",
                            "uid": "10040",
                            "account": "def-pomme-rrg",
                            "cluster_name": "beluga",
                        },
                    "cedar: { ... }
                    "graham: { ... }
                    "mila: { ... }
                }
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
            "google_suite": {
                "id": "%d" % (4000 + n),
                "name": "google_suite_user%0.2d" % n,
                "email": "student%0.2d@mila.quebec" % n,
                "profile_pic": "",
            },
            "cw": {"status": status, "clockwork_api_key": "000aaa%0.2d" % n},
            "accounts_on_clusters": {
                "mila": {
                    "username": "milauser%0.2d" % n,
                    "uid": "%d" % (10000 + n),
                    "account": "mila",
                    "cluster_name": "mila",  # redundant
                }
            },
        }
        # then add the entries for all the clusters on CC
        account = L_cc_accounts[n % 2]
        for cluster_name in L_cc_clusters:
            D_user["accounts_on_clusters"][cluster_name] = {
                "username": "ccuser%0.2d" % n,
                "uid": "%d" % (10000 + n),
                "account": account,
                "cluster_name": cluster_name,
            }
        return D_user

    return [gen_single_user(n) for n in range(N)]


def get_predefined_fake_users_old():

    M = 10

    L_cc_clusters = ["beluga", "graham", "cedar", "narval"]

    LD_users = []
    n = 0
    for _ in range(M):
        for account in [
            "def-patate-rrg",
            "def-pomme-rrg",
            "def-cerise-rrg",
            "def-citron-rrg",
        ]:
            for cluster_name in L_cc_clusters:
                n = n + 1
                LD_users.append(
                    {
                        "username": "ccuser%0.2d" % n,
                        "uid": "%d" % (10000 + n),
                        "account": account,
                        "cluster_name": cluster_name,
                    }
                )

    for _ in range(M):
        for __ in range(
            len(L_cc_clusters)
        ):  # compensate for the other one getting 4x accounts
            account = "mila"
            cluster_name = "mila"
            n = n + 1
            LD_users.append(
                {
                    "username": "milauser%0.2d" % n,
                    "uid": "%d" % (10000 + n),
                    "account": "mila",
                    "cluster_name": "mila",
                }
            )
    return LD_users


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
