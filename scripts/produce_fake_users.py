"""
Generates a json file with fake users to be used by
"anonymize_scontrol_report.py".

"""

import re
import os
import argparse
import json


def get_predefined_fake_users():

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
        for __ in range(len(L_cc_clusters)):  # compensate for the other one getting 4x accounts
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
        json.dump(LD_users, f_out)
        print(f"Wrote {args.output_file}.")


if __name__ == "__main__":
    import sys
    main(sys.argv)

