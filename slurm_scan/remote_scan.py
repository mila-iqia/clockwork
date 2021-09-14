"""
This is the script that collects the Slurm information on remote clusters.
This is to be run at Mila in production as regularly as a cron job,
with a frequency selected to avoid hammering the remote clusters.

One good approach would be to ask for --sinfo only infrequently
because the node specifications don't change very quickly,
and with --sacct more frequently.

This script needs to know to which mongo database it should connect,
through the --mongodb_connection_string argument, and it also offers
the possibility of selecting a different collection for insertion
with the --mongodb_collection argument.

The default setup will add jobs and nodes to
    clockwork/jobs
    clockwork/nodes
which is where the web server will expect to find them.

All the information required to login to the remote clusters
will be found in the json file described by the --cluster_desc argument.
This will also contain a "name" field (ex: "beluga", "graham")
which will be used to tag the entries when committed to mongodb.
The structure of this file is not explained anywhere,
but can be deduced by the four files included, representing the
clusters that are relevant to Mila.

"""

import os
import json
import argparse

# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy, ssh_exception

from helper_sacct import get_job_desc_from_stdout, get_remote_cmd

# See at the end of this script for the argparse definitions.

def main(
    cluster_desc,
    mongodb_connection_string,
    want_sacct=True,
    want_sinfo=True):

    cmd = get_remote_cmd()

    # make the ssh_cmd string
    ssh_cmd = "CHANGE ME " + cmd

    # Nope, not subprocess, but with paramiko.
    # subprocess.check_output(ssh_cmd, shell=True, encoding='utf8')
    # stdout = subprocess.check_output(cmd, shell=True, encoding='utf8')
    stdout = "CHANGE ME"

    LD_jobs = get_job_desc_from_stdout(stdout)

    # Continue here...
    #
    # Do DB stuff and then close.

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Calls sacct and sinfo on a remote machine part of a Slurm cluster.')
    parser.add_argument('--cluster_desc', type=str, default="./cluster_desc/mila.json",
                        help='path to a json file that has all the information on the cluster')
    parser.add_argument('--mongodb_connection_string', type=str, default="",
                        help='connection string to be used by MongoClient')
    parser.add_argument('--mongodb_collection', type=str, default="clockwork",
                        help='which collection are we going to populate')

    # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse#15008806
    parser.add_argument('--sacct', dest='want_sacct', action='store_true')
    parser.add_argument('--no-sacct', dest='want_sacct', action='store_false')
    parser.add_argument('--sinfo', dest='want_sinfo', action='store_true')
    parser.add_argument('--no-sinfo', dest='want_sinfo', action='store_false')
    parser.set_defaults(want_sacct=True, want_sinfo=True)

    args = parser.parse_args()

    # The command line argument "--cluster_desc" is the path to a file,
    # and the argument `cluster_desc` to `main` is the contents of the file.
    if not os.path.exists(args.cluster_desc):
        print(f"Cannot find cluster description. Missing file {args.cluster_desc}.")
        quit()
    else:
        with open(args.cluster_desc, "r") as f:
            cluster_desc = json.load(f)

    if args.mongodb_collection.endswith("jobs") or args.mongodb_collection.endswith("nodes"):
        print("There is a good chance that you are not using the --mongodb_collection properly.\n"
              "The 'jobs' or 'nodes' suffix is added automatically. Don't add it yourself."
        )
        quit()

    main(   cluster_desc=cluster_desc,
            mongodb_connection_string=args.mongodb_connection_string,
            mongodb_collection=args.mongodb_collection,
            want_sacct=args.want_sacct,
            want_sinfo=args.want_sinfo)