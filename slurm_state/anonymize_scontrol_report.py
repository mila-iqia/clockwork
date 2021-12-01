"""
To be run as standalone script, manually, in order to produce
anonymized version of the scontrol reports that can be used
for testing without causing issues with sensitive data.
The input of this script should NOT be shared in github,
but its output definitely can be shared.

This script is not expected to be run automatically as part
of the regular pipeline, but can be run once in a while
when we want to refresh our fake data to reflect potentially
a new configuration of the cluster.
"""

import re
import argparse
import json
import numpy as np


def get_random_job_name():
    return "somejobname_%d" % np.random.randint(low=0, high=1e6)


def get_machine_name(cluster_name, n):
    return {
        "mila": "mil",
        "beluga": "blg",
        "graham": "grh",
        "cedar": "ced",
        "narval": "nar",
    }[cluster_name] + ("%0.4d" % int(n))


def get_random_path():
    return "/a%d/b%d/c%d" % (
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
    )


def process_line(line: str, D_cluster_account: dict) -> str:
    """
    Anonymize the lines from the report.
    This involves doing a hatchet job to some fields
    while keeping other fields intact.
    The assumption is that scontrol is very predictible
    in the layout of its outputs so we can parse things
    with regex.

    D_cluster_account looks like
    {
        "username": "ccuser040",
        "uid": 10040,
        "account": "def-pomme-rrg",
        "cluster_name": "beluga",
    }

    """

    # jobs
    if m := re.match(r"(\s*)(JobId=.+?)\s(JobName=.+?)\s*", line):
        return "%sJobId=%d JobName=%s\n" % (
            m.group(1),
            np.random.randint(low=0, high=1e6),
            get_random_job_name(),
        )
    if m := re.match(r"(\s*)(UserId=.+?)\s(GroupId=.+?)\s(MCS_label=.+?)\s*", line):
        return "%sUserId=%s(%d) GroupId=%s(%d) MCS_label=N/A\n" % (
            m.group(1),
            D_cluster_account["username"],
            D_cluster_account["uid"],
            D_cluster_account["username"],
            D_cluster_account["uid"],
        )
    if m := re.match(r"(.+)(Account=.+?)\s(.+)", line):
        return "%sAccount=%s %s\n" % (
            m.group(1),
            D_cluster_account["account"],
            m.group(3),
        )
    if m := re.match(r"(\s*)(Command=.+?)\s*", line):
        return "%sCommand=%s\n" % (m.group(1), get_random_path())
    if m := re.match(r"(\s*)(WorkDir=.+?)\s*", line):
        return "%sWorkDir=%s\n" % (m.group(1), get_random_path())
    if m := re.match(r"(\s*)(StdErr=.+?)\s*", line):
        return "%sStdErr=%s.err\n" % (m.group(1), get_random_path())
    if m := re.match(r"(\s*)(StdIn=.+?)\s*", line):
        return "%sStdIn=/dev/null\n" % (m.group(1),)
    if m := re.match(r"(\s*)(StdOut=.+?)\s*", line):
        return "%sStdOut=%s.out\n" % (m.group(1), get_random_path())
    if m := re.match(r"(\s*)Partition=.*", line):
        return "%sPartition=fun_partition \n" % (m.group(1),)

    # nodes
    if m := re.match(
        r"(\s*)NodeName=(\w+?)(\d+)\s(Arch=.+?)\s(CoresPerSocket=.+?)\s*", line
    ):
        return "%sNodeName=%s %s %s\n" % (
            m.group(1),
            get_machine_name(D_cluster_account["cluster_name"], m.group(3)),
            m.group(4),
            m.group(5),
        )
    if m := re.match(r"(\s*)(OS=.+?)\s*", line):
        return "%sOS=Linux 17.10.x86_64\n" % (m.group(1),)
    if m := re.match(r"(\s*)NodeAddr=\w+?(\d+)\sNodeHostName=\w+?(\d+)(.*)", line):
        return "%sNodeAddr=%s NodeHostName=%s %s\n" % (
            m.group(1),
            get_machine_name(D_cluster_account["cluster_name"], m.group(3)),
            get_machine_name(D_cluster_account["cluster_name"], m.group(3)),
            m.group(4),
        )
    if m := re.match(r"(\s*)Partitions=", line):
        return "%sPartitions=fun_partitions \n" % (m.group(1),)
    if m := re.match(r"(\s*)Reason=.*", line):
        return "%sReason=partying \n" % (m.group(1),)

    return line


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Take a report from scontrol and strip out all identifying information.",
    )

    parser.add_argument(
        "-c",
        "--cluster_name",
        help="The cluster name. Helps with generating plausible users.",
    )
    parser.add_argument("-i", "--input_file", help="The jobs or nodes report file.")
    parser.add_argument("-u", "--users_file", help="Description of the fake users.")
    parser.add_argument("-o", "--output_file", help="Output file.")
    parser.add_argument(
        "-k",
        "--keep",
        type=int,
        default=None,
        help="Number of values to keep. Ignore the rest.",
    )

    args = parser.parse_args(argv[1:])
    print(args)

    with open(args.users_file, "r") as f:
        LD_users = json.load(f)

    # Sanity check: let's make sure the cluster we're talking about
    # was mentioned in some of the users from LD_users.
    LD_users_on_that_cluster = list(
        filter(
            lambda D_user: args.cluster_name in D_user["accounts_on_clusters"], LD_users
        )
    )
    assert len(LD_users_on_that_cluster)
    D_user = None
    nbr_processed = 0

    with open(args.input_file, "r") as f_in:
        with open(args.output_file, "w") as f_out:
            for line in f_in.readlines():
                # pick a new user every time we hit an empty line
                if D_user is None or re.match(r"^\s*$", line):
                    D_user = np.random.choice(LD_users_on_that_cluster)
                    D_cluster_account = D_user["accounts_on_clusters"][
                        args.cluster_name
                    ]
                    nbr_processed = nbr_processed + 1
                    if args.keep and (args.keep <= nbr_processed - 1):
                        quit()
                f_out.write(process_line(line, D_cluster_account))


if __name__ == "__main__":
    import sys

    main(sys.argv)

"""
python3 anonymize_scontrol_report.py \
    --cluster_name beluga \
    --input_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --output_file ../tmp/slurm_report/beluga/scontrol_show_job_anonymized

python3 anonymize_scontrol_report.py \
    --cluster_name beluga \
    --input_file ../tmp/slurm_report/beluga/scontrol_show_node \
    --output_file ../tmp/slurm_report/beluga/scontrol_show_node_anonymized




"""
