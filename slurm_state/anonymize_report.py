"""
To be run as standalone script, manually, in order to produce
anonymized version of the sacct or sinfo reports that can be used
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

"""
D_job_arrays_delta is used to keep a coherence between job arrays IDs
and the IDs of the jobs they contain. It has the following format:

{
    "<old_job_array>": "<difference between the old job array ID and the new one>",
    "<other_old_job_array>": "<other difference between the old job array ID and the new one>",
    ...
}
"""
D_job_arrays_delta = {}


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

def anonymize_node(D_raw_node: dict, D_cluster_account:dict):
    """
    Anonymize a node

    The anonymization is done as follows:
    - a new name is created from the actual name and the cluster on which the node is
    - a new address is created from the actual address and the cluster on which the node is
    - a new hostname is created from the actual hostname and the cluster on which the node is
    - the operating system is always set to "Linux 17.10.x86_64"
    - the partitions are always "fun_partition" and "other_fun_partition"
    - the reason is always "partying"
    - the "architecture", "last_busy" and "gres" parts remain unchanged
    - the other fields are ignored.
    
    Parameters:
        D_raw_node          The input node, to be anonymized
        D_cluster_account   Dictionary containing user information related to its
                            use of a specific cluster. It has the following structure:
                            { \
                                "username": "ccuser040", \
                                "uid": 10040, \
                                "account": "def-pomme-rrg", \
                                "cluster_name": "beluga" \
                            }

    Returns a dictionary describing an anonymized version of the input node
    """
    # Initialize the anonymized node
    D_anonymized_node = {}

    # For each element of the raw node, anonymize, don't modify or ignore the information
    for (k,v) in D_raw_node.items():
        if k == "name":
            # A new name is created from the actual name and the cluster on which the node is
            D_anonymized_node[k] = get_machine_name(D_cluster_account["cluster_name"], D_raw_node["name"])

        elif k == "address":
            # A new address is created from the actual name and the cluster on which the node is
            D_anonymized_node[k] = get_machine_name(D_cluster_account["cluster_name"], D_raw_node["address"])

        elif k == "hostname":
            # A new hostname is created from the actual name and the cluster on which the node is
            D_anonymized_node[k] = get_machine_name(D_cluster_account["cluster_name"], D_raw_node["hostname"])

        elif k == "operating_system":
            # The operating system is always the same
            D_anonymized_node[k] = "Linux 17.10.x86_64"

        elif k == "partitions":
            # The partitions are always "fun_partition" and "other_fun_partition"
            D_anonymized_node[k] = ["fun_partition", "other_fun_partition"]

        elif k == "reason":
            # The reason is always "partying"
            D_anonymized_node[k] = "partying"

        elif k in ["architecture", "last_busy", "gres"]:
            # Don't modify the value
            D_anonymized_node[k] = v

        # Other fields are ignored
        # This is done in order to "filter" what information passes if the sinfo
        # structure evolves or if we have not chosen yet how to "anonymize" one of the fields

    # Returns the anonymized node
    return D_anonymized_node


def anonymize_job(D_raw_job: dict, D_cluster_account:dict):
    """
    Anonymize a job

    The anonymization is done as follows:
    - a random job ID is generated, as an integer whose value lays within the range [0,1e6]
    - the task ID within the job array remains unchanged
    - a random job array ID is generated, as an integer whose value lays within the range [0,1e6]
      However, it is important to underline that a precedence relation is kept between the job ID
      and its associated job array ID, if appliable
    - a random job name is generated
    - the user and group are defined from the cluster account passed as parameter (D_cluster_account)
    - the account is defined from the cluster account passed as parameter (D_cluster_account)
    - the association dictionary is defined from the cluster account passed as parameter (D_cluster_account)
    - the cluster is defined from the cluster name contained in the cluster account passed as parameter (D_cluster_account)
    - a random path is generated to be used as the working directory of the job
    - the partition is always "fun_partition" or "other_fun_partition"
    - new nodes names are defined by combining a cluster identifier and the node(s) name(s)
    - the other fields are ignored.

    Parameters:
        D_raw_job           The input job, to be anonymized
        D_cluster_account   Dictionary containing user information related to its
                            use of a specific cluster. It has the following structure:
                            { \
                                "username": "ccuser040", \
                                "uid": 10040, \
                                "account": "def-pomme-rrg", \
                                "cluster_name": "beluga" \
                            }

    Returns a dictionary describing an anonymized version of the input job
    """
    # Initialize the anonymized job
    D_anonymized_job = {}

    # For each element of the raw job, anonymize, don't modify or ignore the information
    for (k,v) in D_raw_job.items():
        if k == "job_id":
            # The job ID and the JobArray ID have a precedence relation, thus both are set here

            if D_raw_job["array"]["job_id"] == 0:
                # The current job is a single job

                # The default values for an empty array are set for the "array" element
                D_anonymized_job["array"] = {
                    "job_id": 0,
                    "limits": {
                        "max": {
                            "running": {
                            "tasks": 0
                            }
                        }
                    },
                    "task": None,
                    "task_id": None
                }

                # A random job ID is generated, as an integer whose value lays within the range [0,1e6]
                D_anonymized_job["job_id"] = np.random.randint(low=0, high=1e6)
 
            else:
                # The job is part of a job array. We store the ID of this job array
                # in a variable
                previous_job_array_id = D_raw_job["array"]["job_id"]

                if previous_job_array_id not in D_job_arrays_delta:
                    # If it is the first time this job array has been encountered
                    # while parsing, generate a random array job ID, as an integer
                    # whose value lays within the range [0,1e6]
                    new_job_array_id = np.random.randint(low=0, high=1e6)

                    # Compute the delta between the previous job array ID and the
                    # new one
                    delta = new_job_array_id - previous_job_array_id

                    # Store this value in D_job_arrays_delta
                    D_job_arrays_delta[previous_job_array_id] = delta

                else:
                    # If it is not the first time this job array has been encountered,
                    # retrieve the associated delta which will be used to compute
                    # the IDs
                    delta = D_job_arrays_delta[previous_job_array_id]


                # Store the new job array data
                D_anonymized_job["array"] = {
                    "job_id": previous_job_array_id + delta,
                    "limits": D_raw_job["array"]["limits"],
                    "task": None,
                    "task_id": D_raw_job["array"]["task_id"]
                }

                # Compute the new job ID from the delta
                D_anonymized_job["job_id"] = D_raw_job["job_id"] + delta

            

        elif k == "name":
            # A new job name is generated
            D_anonymized_job[k] = get_random_job_name()
        
        elif k == "user" or k == "group":
            # Use the cluster account information passed as argument to define the username or group
            D_anonymized_job[k] = D_cluster_account["username"]

        elif k == "account":
            # Use the cluster account information passed as argument to define the account
            D_anonymized_job[k] = D_cluster_account["account"]

        elif k == "association":
            # The association is formatted as follows:
            # "association": {
            #    "account": "mila",
            #    "cluster": "mila",
            #    "partition": null,
            #    "user": "student00"
            # }
            #
            # Use the cluster account information passed as argument to define the account and user
            D_anonymized_job[k] = {
                "account": D_cluster_account["account"],
                "cluster": D_cluster_account["cluster_name"],
                "partition": None,
                "user": D_cluster_account["username"]
            }

        elif k == "cluster":
            # Use the cluster account information passed as argument to define the cluster name
            D_anonymized_job[k] = D_cluster_account["cluster_name"]

        elif k == "working_directory":
            # A random path is generated to be used as the working directory of the job
            D_anonymized_job[k] = get_random_path()

        elif k == "partition":
            # The partition is always "fun_partition" or "other_fun_partition"
            D_anonymized_job[k] = np.random.choice(["fun_partition", "other_fun_partition"])
        
        elif k == "nodes":
            # The value of the "nodes" element could take similar formats:
            # - "None assigned" if no node has been yet assigned to the job
            # - "cn-f001" if the node cn-f001 has been associated to the job
            # - "cn-f[001-002]" if the nodes cn-f001 and cn-f002 have been associated to the job
            # - cf-f[001,004-007,009-010,012] if the nodes cn-f001, cn-f004, cn-f005, cn-f006, cn-f007, cn-f009, cn-f010 and cn-f012 has been associated to the job
            #
            # We then use the same function as the one used for the nodes: it combines a cluster identifier and the node(s) name(s)
            D_anonymized_job[k] = get_machine_name(D_cluster_account["cluster_name"], v)

        elif k in ["allocation_nodes", "exit_code", "derived_exit_code", "time", "flags", "tres", "state"]:
            # Don't modify the value
            D_anonymized_job[k] = v

        # Other fields are ignored
        # This is done in order to "filter" what information passes if the sacct
        # structure evolves or if we have not chosen yet how to "anonymize" one of the fields

    # Returns the anonymized job
    return D_anonymized_job


def main(argv):
    # Define the input
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Take a report from sacct or sinfo and strip out all identifying information.",
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

    # Retrieve the input arguments
    args = parser.parse_args(argv[1:])

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
            # Initialize the data to output
            output_data = {}
            # Load the sacct or sinfo data
            input_data = json.load(f_in)
            for (k,v) in input_data.items():
                if k == "nodes" or k == "jobs":
                    # Initialize an empty jobs or nodes list. The jobs and nodes
                    # will then be anonymized before be added to that list.
                    output_data[k] = []

                    # Here, "entity" is a common term to qualify a job or a node
                    for entity in input_data[k]:
                        # Pick a random new user to associate to the job or node
                        D_user = np.random.choice(LD_users_on_that_cluster)
                        D_cluster_account = D_user["_extra"][args.cluster_name]
                        
                        # Anonymize the job or node
                        if k == "nodes":
                            anonymized_entity = anonymize_node(entity, D_cluster_account)
                        else:
                            anonymized_entity = anonymize_job(entity, D_cluster_account)
                        # Append the anonymized job or node to the output
                        output_data[k].append(anonymized_entity)


                        # If the requested number of entities in the output file
                        # is reached, stop the loop
                        nbr_processed = nbr_processed + 1
                        if args.keep and (args.keep <= nbr_processed - 1):
                            break

                else:
                    output_data[k] = v

            # Store the output data in the output file
            json.dump(output_data, f_out)


if __name__ == "__main__":
    import sys

    main(sys.argv)

"""
python3 anonymize_report.py \
    --cluster_name beluga \
    --input_file ../tmp/slurm_report/beluga/sacct_report \
    --output_file ../tmp/slurm_report/beluga/sacct_report_anonymized

python3 anonymize_scontrol_report.py \
    --cluster_name beluga \
    --input_file ../tmp/slurm_report/beluga/sinfo_report \
    --output_file ../tmp/slurm_report/beluga/sinfo_report_anonymized




"""
