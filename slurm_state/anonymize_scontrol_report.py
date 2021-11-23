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
import os
import argparse

import numpy as np


def get_account_name():
    return np.random.choice(
        ["def-patate-rrg", "def-pomme-rrg", "def-cerise-rrg", "def-citron-rrg"]
    )


def get_random_name():
    return "somename_%d" % np.random.randint(low=0, high=1e6)


def get_random_username():
    return np.random.choice(["mario", "luigi", "toad", "peach"])


# def get_random_node_name():
#     return np.random.choice(["beast", "machine", "derp", "engine"]) + ("%0.4d" % np.random.randint(low=0, high=1e5))


def get_random_path():
    return "/a%d/b%d/c%d" % (
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
    )


def process_line(line):
    """
    Anonymize the lines from the report.
    This involves doing a hatchet job to some fields
    while keeping other fields intact.
    The assumption is that scontrol is very predictible
    in the layout of its outputs so we can parse things
    with regex.
    """

    # jobs
    if m := re.match(r"(\s*)(JobId=.+?)\s(JobName=.+?)\s*", line):
        return "%sJobId=%d JobName=%s\n" % (
            m.group(1),
            np.random.randint(low=0, high=1e6),
            get_random_name(),
        )
    if m := re.match(r"(\s*)(UserId=.+?)\s(GroupId=.+?)\s(MCS_label=.+?)\s*", line):
        u = get_random_username()
        d = np.random.randint(low=0, high=1e6)
        return "%sUserId=%s(%d) GroupId=%s(%d) MCS_label=N/A\n" % (
            m.group(1),
            u,
            d,
            u,
            d,
        )
    if m := re.match(r"(.+)(Account=.+?)\s(.+)", line):
        return "%sAccount=%s %s\n" % (m.group(1), get_account_name(), m.group(3))
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
        return "%sNodeName=%s%s %s %s\n" % (
            m.group(1),
            "machine",
            m.group(3),
            m.group(4),
            m.group(5),
        )
    if m := re.match(r"(\s*)(OS=.+?)\s*", line):
        return "%sOS=Linux 17.10.x86_64\n" % (m.group(1),)
    if m := re.match(r"(\s*)NodeAddr=\w+?(\d+)\sNodeHostName=\w+?(\d+)(.*)", line):
        return "%sNodeAddr=%s%s NodeHostName=%s%s %s\n" % (
            m.group(1),
            "machine",
            m.group(2),
            "machine",
            m.group(3),
            m.group(4),
        )
    if m := re.match(r"(\s*)Partitions=", line):
        return "%sPartitions=fun_partitions \n" % (m.group(1),)

    return line


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Take a report from scontrol and strip out all identifying information.",
    )

    parser.add_argument("-i", "--input_file", help="The jobs or nodes report file.")
    parser.add_argument("-o", "--output_file", help="Output file.")

    args = parser.parse_args(argv[1:])
    print(args)

    with open(args.input_file, "r") as f_in:
        with open(args.output_file, "w") as f_out:
            for line in f_in.readlines():
                f_out.write(process_line(line))


if __name__ == "__main__":
    import sys

    main(sys.argv)

"""
python3 anonymize_scontrol_report.py \
    --input_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --output_file ../tmp/slurm_report/beluga/scontrol_show_job_anonymized

python3 anonymize_scontrol_report.py \
    --input_file ../tmp/slurm_report/beluga/scontrol_show_node \
    --output_file ../tmp/slurm_report/beluga/scontrol_show_node_anonymized


"""
