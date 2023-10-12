"""
The sinfo parser is used to convert nodes retrieved through a sinfo command on a cluster
to nodes in the format used by Clockwork.
"""

import json, os

# Imports to retrieve the values related to sinfo call
from slurm_state.helpers.ssh_helper import open_connection
from slurm_state.helpers.clusters_helper import get_all_clusters

# These functions are translators used in order to handle the values
# we could encounter while parsing a node dictionary retrieved from a
# sinfo command.
from slurm_state.helpers.parser_helper import (
    copy,
    copy_with_none_as_empty_string,
    rename,
)

# This map should contain all the fields that come from parsing a node entry
# Each field should be mapped to a handler that will process the string data
# and set the result in the output dictionary. Fields not associated to any
# parsing function are ignored.

NODE_FIELD_MAP = {
    "architecture": rename("arch"),
    "comment": copy,
    "cores": copy,
    "cpus": copy,
    "last_busy": copy,
    "features": copy,
    "gres": copy_with_none_as_empty_string,
    "gres_used": copy,
    "name": copy,
    "address": rename("addr"),
    "state": copy,
    "state_flags": copy,
    "real_memory": rename("memory"),
    "reason": copy,
    "reason_changed_at": copy,
    "tres": copy,
    "tres_used": copy,
}


# The node parser itself
def node_parser(f):
    """
    This function parses a report retrieved from a sinfo command (JSON format).
    It acts as an iterator, over all the parsed nodes.

    This is an example of such a command:
        sinfo --json


    Here is an example of some fields that could be encountered in a node of some
    fictitious (and illogical) values associated to these fields:
        {
            "architecture": "x86_64",
            "burstbuffer_network_address": "",
            "boards": 1,
            "boot_time": 1679345346,
            "comment": "",
            "cores": 20,
            "cpu_binding": 0,
            "cpu_load": 2000,
            "extra": "",
            "free_memory": 246,
            "cpus": 40,
            "last_busy": 1681387881,
            "features": "x86_64,turing,48gb",
            "active_features": "x86_64,turing,48gb",
            "gres": "gpu:rtx8000:8(S:0-1)",
            "gres_drained": "N\/A",
            "gres_used": "gpu:rtx8000:8(IDX:0-7),tpu:0",
            "mcs_label": "",
            "name": "node_name",
            "next_state_after_reboot": "invalid",
            "address": "node_addr",
            "hostname": "node_hostname",
            "state": "down",
            "state_flags": [
                "DRAIN"
            ],
            "next_state_after_reboot_flags": [
            ],
            "operating_system": "Linux 4.15.0-194-generic #205-Ubuntu SMP Fri Sep 16 19:49:27 UTC 2022",
            "owner": null,
            "partitions": [
                "debug"
            ],
            "port": 6812,
            "real_memory": 1800,
            "reason": "Sanity Check Failed",
            "reason_changed_at": 1679695880,
            "reason_set_by_user": "root",
            "slurmd_start_time": 1679345380,
            "sockets": 1,
            "threads": 1,
            "temporary_disk": 0,
            "weight": 1,
            "tres": "cpu=40,mem=386618M,billing=96,gres\/gpu=8",
            "slurmd_version": "23.02.1-ex",
            "alloc_memory": 0,
            "alloc_cpus": 0,
            "idle_cpus": 2,
            "tres_used": "cpu=26,mem=249G,gres\/gpu=8",
            "tres_weighted": 0
        },

    The expected output would then be these associations of keys and values:
        {
            "arch": "x86_64",
            "comment": "",
            "cores": 20,
            "cpus": 40,
            "last_busy": 1681387881,
            "features": "x86_64,turing,48gb",
            "gres": gpu:rtx8000:8(S:0-1),
            "name": "node_name",
            "address": "node_addr",
            "state": "down",
            "memory": 1800,
            "reason": "Sanity Check Failed",
            "reason_changed_at": 1679695880,
            "tres": "cpu=40,mem=386618M,billing=96,gres\/gpu=8",
            "tres_used": "cpu=26,mem=249G,gres\/gpu=8"
        }

    Parameters:
        f       JSON report retrieved from a sinfo command
    """
    # Load the JSON file generated by the sinfo command
    sinfo_data = json.load(f)
    # at this point, sinfo_data is a hierarchical structure of dictionaries and lists

    src_nodes = sinfo_data["nodes"]  # nodes is a list

    for src_node in src_nodes:
        res_node = (
            dict()
        )  # Initialize the dictionary which will store the newly formatted node data

        for k, v in src_node.items():
            # We will use a handler mapping to translate this
            translator = NODE_FIELD_MAP.get(k, None)

            if translator is not None:
                # Translate using the translator retrieved from JOB_FIELD_MAP
                translator(k, v, res_node)

            # If no translator has been provided: ignore the field

        yield res_node


# The functions used to create the report file, gathering the information to parse


def generate_node_report(
    cluster_name,
    file_name,
):
    """
    Launch a sinfo command in order to retrieve JSON report containing
    nodes information

    Parameters:
        cluster_name        The name of the cluster on which the sinfo command will be launched
        file_name           The path of the report file to write

    """
    # Retrieve the cluster's information from the configuration file
    cluster = get_all_clusters()[cluster_name]

    # Retrieve from the configuration file the elements used to establish a SSH connection
    # to a remote cluster and launch the sinfo command on it
    username = cluster[
        "remote_user"
    ]  # The username used for the SSH connection to launch the sinfo command
    hostname = cluster[
        "remote_hostname"
    ]  # The hostname used for the SSH connection to launch the sinfo command
    port = cluster[
        "ssh_port"
    ]  # The port used for the SSH connection to launch the sinfo command
    sinfo_path = cluster[
        "sinfo_path"
    ]  # The path of the sinfo executable on the cluster side
    ssh_key_filename = cluster[
        "ssh_key_filename"
    ]  # The name of the private key in .ssh folder used for the SSH connection to launch the sinfo command

    # sinfo path checks
    assert (
        sinfo_path
    ), "Error. We have called the function to make updates with sinfo but the sinfo_path config is empty."
    assert sinfo_path.endswith(
        "sinfo"
    ), f"Error. The sinfo_path configuration needs to end with 'sinfo'. It's currently {sinfo_path} ."

    # SSH key check
    assert ssh_key_filename, "Missing ssh_key_filename from config."

    # Now this is the private ssh key that we'll be using with Paramiko.
    ssh_key_path = os.path.join(os.path.expanduser("~"), ".ssh", ssh_key_filename)

    # Set the sinfo command
    remote_cmd = f"{sinfo_path} --json"
    print(f"remote_cmd is\n{remote_cmd}")

    # Connect through SSH
    try:
        ssh_client = open_connection(
            hostname, username, ssh_key_path=ssh_key_path, port=port
        )
    except Exception as inst:
        print(f"Error. Failed to connect to {hostname} to make a call to sinfo.")
        print(inst)
        return []

    if ssh_client:
        # those three variables are file-like, not strings
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(remote_cmd)

        # We should find a better option to retrieve stderr
        """
        response_stderr = "".join(ssh_stderr.readlines())
        if len(response_stderr):
            print(
                f"Stderr in sinfo call on {hostname}. This doesn't mean that the call failed entirely, though.\n{response_stderr}"
            )
        """

        # Create directories if needed
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        # Write the command output to a file
        with open(file_name, "w") as outfile:
            for line in ssh_stdout.readlines():
                outfile.write(line)

        ssh_client.close()
    else:
        print(
            f"Error. Failed to connect to {hostname} to make call to sinfo. Returned `None` but no exception was thrown."
        )
