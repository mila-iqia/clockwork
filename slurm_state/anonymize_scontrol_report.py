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


def get_machine_name(cluster_name, node_name):
    """
    Generate another name for a node, based on its name and its cluster.

    A node called "ab-a001" on the cluster Mila is then called: milab-a001
    for instance.
    """
    return {
        "mila": "mil",
        "beluga": "blg",
        "graham": "grh",
        "cedar": "ced",
        "narval": "nar",
    }[cluster_name] + node_name


def get_random_path():
    """
    Generate a fake path, used to fill the fake data.
    """
    return "/a%d/b%d/c%d" % (
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
        np.random.randint(low=0, high=1000),
    )


def process_line(line: str, D_cluster_account: dict) -> str:
    """
    Anonymize the lines from the report.

    This involves doing a hatchet job to some fields while keeping other fields
    intact. The assumption is that scontrol is very predictible in the layout
    of its outputs so we can parse things with regex.

    D_cluster_account looks like :
    { \
        "username": "ccuser040", \
        "uid": 10040, \
        "account": "def-pomme-rrg", \
        "cluster_name": "beluga" \
    }

    """

    # jobs
    """
    This regex is used to parse lines like the following:
    JobId=1234567 JobName=JesuisunNomdeJob
    or
    JobId=1234567 ArrayJobId=1234566 ArrayTaskId=1 JobName=JesuisunNomdeJob

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, another line is reconstructed, adding a random number as job id,
    and a random job name, beginning with "somejobname_".

    Hence, the returned line could be:
    JobId=1927374 JobName=somejobname_389402


    NB: in the case of lines presenting an ArrayJobId and an ArrayTaskId (ie
    when a job array is used), these two elements are not taken into account.
    For now (?)
    """
    if m := re.match(r"(\s*)(JobId=.+?)\s(JobName=.+?)\s*", line):
        return "%sJobId=%d JobName=%s\n" % (
            m.group(1),
            np.random.randint(low=0, high=1e6),
            get_random_job_name(),
        )

    """
    This regex is used to parse lines like the following:
    UserId=nobody(221774718) GroupId=nobody(221774718) MCS_label=N/A

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, another line is reconstructed, faking a user by using the data
    stored into D_cluster_account.

    Thus, with a D_cluster_account as:
    { \
        "username": "ccuser040", \
        "uid": 10040, \
        "account": "def-pomme-rrg", \
        "cluster_name": "beluga" \
    },

    the returned line would be:
    UserId=ccuser040(10040) GroupId=ccuser040(10040) MCS_label=N/A
    """
    if m := re.match(r"(\s*)(UserId=.+?)\s(GroupId=.+?)\s(MCS_label=.+?)\s*", line):
        return "%sUserId=%s(%d) GroupId=%s(%d) MCS_label=N/A\n" % (
            m.group(1),
            D_cluster_account["username"],
            D_cluster_account["uid"],
            D_cluster_account["username"],
            D_cluster_account["uid"],
        )

    """
    This regex is used to parse lines like the following:
    Priority=1234567 Nice=0 Account=def_acc QOS=normal

    where:
    - m.group(1) is Priority=1234567 Nice=0
    - m.group(2) is Account=def_acc
    - m.group(3) is QOS=normal

    From it, a new line is reconstructed, keeping all elements except the
    Account, which is replaced by using D_cluster_account["account"].

    Thus, with a D_cluster_account as:
    { \
        "username": "ccuser040", \
        "uid": 10040, \
        "account": "def-pomme-rrg", \
        "cluster_name": "beluga" \
    },

    the returned line would be:
    Priority=1234567 Nice=0 Account=def-pomme-rrg QOS=normal
    """
    if m := re.match(r"(.+)(Account=.+?)\s(.+)", line):
        return "%sAccount=%s %s\n" % (
            m.group(1),
            D_cluster_account["account"],
            m.group(3),
        )

    """
    This regex is used to parse lines like the following:
    Command=/tmp/usr/script.sh arg

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a command by using the
    function get_random_path.

    Thus, the returned line could be:
    Command=/a143/b567/c9
    """
    if m := re.match(r"(\s*)(Command=.+?)\s*", line):
        return "%sCommand=%s\n" % (m.group(1), get_random_path())

    """
    This regex is used to parse lines like the following:
    WorkDir=/home/mila/tmp/squalala

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a working directory by using
    the function get_random_path.

    Thus, the returned line could be:
    WorkDir=/a845/b90/c843
    """
    if m := re.match(r"(\s*)(WorkDir=.+?)\s*", line):
        return "%sWorkDir=%s\n" % (m.group(1), get_random_path())

    """
    This regex is used to parse lines like the following:
    StdErr=/home/mila/tmp/errors.txt

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a StdErr by using
    the function get_random_path.

    Thus, the returned line could be:
    StdErr=/a894/b56/c293.err
    """
    if m := re.match(r"(\s*)(StdErr=.+?)\s*", line):
        return "%sStdErr=%s.err\n" % (m.group(1), get_random_path())

    """
    This regex is used to parse lines like the following:
    StdIn=/tmp/pifpafpouf

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a StdIn as /dev/null.

    Thus, the returned line is like:
    StdIn=/dev/null
    """
    if m := re.match(r"(\s*)(StdIn=.+?)\s*", line):
        return "%sStdIn=/dev/null\n" % (m.group(1),)

    """
    This regex is used to parse lines like the following:
    StdOut=/home/mila/tmp/slurm-1234567.out

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a StdOut by using
    the function get_random_path.

    Thus, the returned line could be:
    StdOut=/a938/b46/c123.out
    """
    if m := re.match(r"(\s*)(StdOut=.+?)\s*", line):
        return "%sStdOut=%s.out\n" % (m.group(1), get_random_path())

    """
    This regex is used to parse lines like the following:
    Partition=unkillable AllocNode:Sid=loginx:12345

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, a new line is reconstructed, "faking" a "fun_partition" as
    the Partition

    Thus, the returned line is like:
    Partition=fun_partition
    """
    if m := re.match(r"(\s*)Partition=.*", line):
        return "%sPartition=fun_partition \n" % (m.group(1),)

    # nodes
    """
    This regex is used to parse lines like the following:
    NodeName=cn-a001 Arch=x86_64 CoresPerSocket=20

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file
    - m.group(2) is cn-a001
    - m.group(3) is Arch=x86_64
    - m.group(4) is CoresPerSocket=20

    From it, another line is reconstructed, keeping all elements except the
    NodeName, which is changed by calling the function get_machine_name.

    Thus, in the previous example, the NodeName becomes "milcn-a001" for a
    node in the Mila cluster.

    Hence, the returned line is:
    NodeName=milcn-a001 Arch=x86_64 CoresPerSocket=20
    """
    if m := re.match(
        r"(\s*)NodeName=([\-\w]+?\d+)\s(Arch=.+?)\s(CoresPerSocket=.*)\s*", line
    ):
        return "%sNodeName=%s %s %s\n" % (
            m.group(1),
            get_machine_name(D_cluster_account["cluster_name"], m.group(2)),
            m.group(3),
            m.group(4),
        )

    """
    This regex is used to parse lines like the following:
    OS=Linux 4.10.0-99-generic #Comment about the OS

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, another line is reconstructed, "faking" a Linux 17.10 as OS.
    """
    if m := re.match(r"(\s*)OS=.+?\s*", line):
        return "%sOS=Linux 17.10.x86_64\n" % (m.group(1),)

    """
    This regex is used to parse lines like the following:
    NodeAddr=ab-a001 NodeHostName=ab-a001 Version=20.11.8

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file
    - m.group(2) is ab-a001
    - m.group(3) is ab-a001
    - m.group(4) is Version=20.11.8

    From it, another line is reconstructed, keeping all elements except the
    NodeAddr and the NodeHostName, which are changed by calling the
    function get_machine_name.

    Thus, in the previous example, the NodeAddr and NodeHostName both become
    "cedab-a001" for a node in the Cedar cluster for instance.

    Hence, the returned line is:
    NodeAddr=cedcn-a001 NodeHostName=cedcn-a001 Version=20.11.8
    """
    if m := re.match(
        r"(\s*)NodeAddr=([\-\w]+?\d+)\sNodeHostName=([\-\w]+?\d+)(.*)", line
    ):
        return "%sNodeAddr=%s NodeHostName=%s %s\n" % (
            m.group(1),
            get_machine_name(D_cluster_account["cluster_name"], m.group(2)),
            get_machine_name(D_cluster_account["cluster_name"], m.group(3)),
            m.group(4),
        )

    """
    This regex is used to parse lines like the following:
    Partitions=unkillable,short-unkillable,etc

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, another line is reconstructed, "faking" a "fun_partitions" as
    the partitions
    """
    if m := re.match(r"(\s*)Partitions=", line):
        return "%sPartitions=fun_partitions \n" % (m.group(1),)

    """
    This regex is used to parse lines like the following:
    Reason=NVIDIA Update

    where:
    - m.group(1) is null here, but is used in order to keep the same indentation
      between the input file and the generated file

    From it, another line is reconstructed, "faking" "partying" as
    the reason
    """
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
        filter(lambda D_user: args.cluster_name in D_user["_extra"], LD_users)
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
                    D_cluster_account = D_user["_extra"][args.cluster_name]
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
