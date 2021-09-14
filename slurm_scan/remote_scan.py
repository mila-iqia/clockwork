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
Naturally, the setup for public-key ssh has to be in place
on the host machine for it to connect to the remote cluster.
This is not done by this code.

python3 remote_scan.py --cluster_desc=cluster_desc/mila.json --write_data_to_file=debug.json --no-sinfo
"""

import os
import json
import argparse

# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy, ssh_exception

from helper_sacct import get_jobs_desc_from_stdout, get_remote_sacct_cmd
from helper_sinfo import get_nodes_desc_from_stdout, get_remote_sinfo_cmd

# See at the end of this script for the argparse definitions.

def main(
    cluster_desc,
    mongodb_connection_string="",
    mongodb_collection="clockwork",
    want_mongodb=True,
    want_sacct=True,
    want_sinfo=True,
    write_data_to_file=None):

    with SSHClient() as ssh_client:

        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.load_system_host_keys()

        # The call to .connect was seen to raise an exception now and then.
        #     raise AuthenticationException("Authentication timeout.")
        #     paramiko.ssh_exception.AuthenticationException: Authentication timeout.
        try:
            print(f"Connecting to {cluster_desc['hostname']}.")
            ssh_client.connect(cluster_desc["hostname"], username=cluster_desc["username"], port=cluster_desc["port"])
            print(f"Connected to {cluster_desc['hostname']}.")
        # except ssh_exception.AuthenticationException as inst:
        #     maybe do something different?
        except Exception as inst:
            print(type(inst))
            print(inst)
            quit()

        # Run the desired commands remotely.
        
        #    sacct
        if want_sacct:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(get_remote_sacct_cmd())
            response_str = "\n".join(ssh_stdout.readlines())
            print(response_str)
            if len(response_str) == 0:
                print("Got an empty response from server.")
                print(" ".join(ssh_stderr.readlines()))
                quit()
            LD_jobs = get_jobs_desc_from_stdout(response_str)
        else:
            LD_jobs = None

        #    sinfo
        if want_sinfo:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(get_remote_sinfo_cmd())
            response_str = "\n".join(ssh_stdout.readlines())
            if len(response_str) == 0:
                print("Got an empty response from server.")
                print(" ".join(ssh_stderr.readlines()))
                quit()
            LD_nodes = get_nodes_desc_from_stdout(response_str)
        else:
            LD_nodes = None

    # ssh_client.close()

    data = {"jobs": LD_jobs, "nodes": LD_nodes}

    # Continue here...
    # TODO : Do DB stuff and then close.

    if write_data_to_file is not None or write_data_to_file:
        with open(write_data_to_file, "w") as f:
            json.dump(data, f, indent=4)
            print(f"Wrote {write_data_to_file}.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Calls sacct and sinfo on a remote machine part of a Slurm cluster.')
    parser.add_argument('--cluster_desc', type=str, default="./cluster_desc/mila.json",
                        help='Path to a json file with all the information about the target cluster.')
    parser.add_argument('--mongodb_connection_string', type=str, default="",
                        help='Connection string to be used by MongoClient. Ignored if --no_mongodb is set.')
    parser.add_argument('--mongodb_collection', type=str, default="clockwork",
                        help='Collection to populate. Ignored if --no_mongodb is set.')
    # for debugging and testing, especially in conjunction with "--no-mongodb"
    parser.add_argument('--write_data_to_file', type=str, default=None,
                        help='Writes the data to a file specified by that path (when specified). Assumes the parent directory already exists.')

    # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse#15008806
    parser.add_argument('--sacct', dest='want_sacct', action='store_true')
    parser.add_argument('--no-sacct', dest='want_sacct', action='store_false')
    parser.add_argument('--sinfo', dest='want_sinfo', action='store_true')
    parser.add_argument('--no-sinfo', dest='want_sinfo', action='store_false')
    # disabling mongodb might be useful for debugging and testing
    parser.add_argument('--mongodb', dest='want_mongodb', action='store_true')
    parser.add_argument('--no-mongodb', dest='want_mongodb', action='store_false')
    parser.set_defaults(want_sacct=True, want_sinfo=True, want_mongodb=True)

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
            want_mongodb=args.want_mongodb,
            want_sacct=args.want_sacct,
            want_sinfo=args.want_sinfo,
            write_data_to_file=args.write_data_to_file)