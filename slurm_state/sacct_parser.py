"""
The sacct parser is used to convert jobs retrieved through a sacct command on a cluster
to jobs in the format used by Clockwork.
"""
import json, os

# Imports related to sacct call
# https://docs.paramiko.org/en/stable/api/client.html
from slurm_state.helpers.ssh_helper import open_connection

from slurm_state.extra_filters import clusters_valid, get_allocations
from slurm_state.config import get_config, string, optional_string, timezone

clusters_valid.add_field("sacct_path", optional_string)
clusters_valid.add_field("ssh_key_filename", string)
clusters_valid.add_field("timezone", timezone)
clusters_valid.add_field("remote_user", optional_string)
clusters_valid.add_field("remote_hostname", optional_string)

# These functions are translators used in order to handle the values
# we could encounter while parsing a job dictionary retrieved from a
# sacct command.
from slurm_state.helpers.parser_helper import copy, rename

# The following functions are only used by the job parser. Translator
# functions shared with the node parser are retrieved from
# slurm_state.helpers.parser_helper.


def copy_and_stringify(k, v, res):
    res[k] = str(v)


def rename_subitems(subitem_dict):
    def renamer(k, v, res):
        for subitem, name in subitem_dict.items():
            res[name] = v[subitem]

    return renamer


def translate_with_value_modification(v_modification, translator, **args):
    """
    This function returns a translator that includes a modification
    on the value which will be transmitted to it

    Parameters:
        v_modification  The function modifying the value before it
                        is transmitted to the translator
        translator      The translator called

    Returns:
        A translator function including the expected value modification
    """
    # Some translator can depend on specific arguments. Thus, we call
    # them before to apply it and get the translator which has to be
    # used
    final_translator = translator(**args)

    # This helper is used to update the value v before applying the
    # translator on the triplet (k, v, res)
    def combiner(k, v, res):
        final_translator(k, v_modification(v), res)

    return combiner


def zero_to_null(v):
    """
    Convert the value from 0 to null

    Parameter:
        v   The values to be converted if appliable

    Return:
        The converted values
    """
    # If a value of v equals 0, transform it to None
    for (v_k, v_v) in v.items():
        if v_v == 0:
            v[v_k] = None
    # Return v
    return v


def rename_and_stringify_subitems(subitem_dict):
    def renamer(k, v, res):
        for subitem, name in subitem_dict.items():
            res[name] = str(v[subitem])

    return renamer


def join_subitems(separator, name):
    def joiner(k, v, res):
        values = []
        for _, value in v.items():
            values.append(str(value))
        res[name] = separator.join(values)

    return joiner


def extract_tres_data(k, v, res):
    """
    Extract count of the elements present in the value associated to the key "tres"
    in the input dictionary. Such a dictionary would present a structure similar as depicted below:
        "tres": {
            'allocated': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ],
            'requested': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ]
        }

    The dictionaries (and their associated keys) inserted in the job result by this function
    for this input should be:
        "tres_allocated": {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }
        "tres_requested": {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }
    """

    def get_tres_key(tres_type, tres_name):
        """
        Basically, this function is used to rename the element
        we want to retrieve regarding the TRES type (as we are
        for now only interested by the "count" of the entity)
        """
        if tres_type == "mem" or tres_type == "billing":
            return tres_type
        elif tres_type == "cpu":
            return "num_cpus"
        elif tres_type == "gres":
            if tres_name == "gpu":
                return "num_gpus"
            else:
                return "gres"
        elif tres_type == "node":
            return "num_nodes"
        else:
            return None

    tres_subdict_names = [
        {"sacct_name": "allocated", "cw_name": "tres_allocated"},
        {"sacct_name": "requested", "cw_name": "tres_requested"},
    ]
    for tres_subdict_name in tres_subdict_names:
        res[
            tres_subdict_name["cw_name"]
        ] = {}  # Initialize the "tres_allocated" and the "tres_requested" subdicts
        for tres_subdict in v[tres_subdict_name["sacct_name"]]:
            tres_key = get_tres_key(
                tres_subdict["type"], tres_subdict["name"]
            )  # Define the key associated to the TRES
            if tres_key:
                res[tres_subdict_name["cw_name"]][tres_key] = tres_subdict[
                    "count"
                ]  # Associate the count of the element, as value associated to the key defined previously


# This map should contain all the fields that come from parsing a job entry
# Each field should be mapped to a handler that will process the string data
# and set the result in the output dictionary. Fields not associated to any
# parsing function are ignored.

JOB_FIELD_MAP = {
    "account": copy,
    "array": rename_and_stringify_subitems(
        {"job_id": "array_job_id", "task_id": "array_task_id"}
    ),
    "cluster": rename("cluster_name"),
    "exit_code": join_subitems(":", "exit_code"),
    "job_id": copy_and_stringify,
    "name": copy,
    "nodes": copy,
    "partition": copy,
    "state": rename_subitems({"current": "job_state"}),
    "time": translate_with_value_modification(
        zero_to_null,
        rename_subitems,
        subitem_dict={
            "limit": "time_limit",
            "submission": "submit_time",
            "start": "start_time",
            "end": "end_time",
        },
    ),
    "tres": extract_tres_data,
    "user": rename("username"),
    "working_directory": copy,
}


# The job parser itself
def job_parser(f):
    """
    This function parses a report retrieved from a sacct command (JSON format).
    It acts as an iterator, over all the parsed jobs.

    This is an example of such a command:
        /opt/software/slurm/bin/sacct -A rrg-bengioy-ad_gpu,rrg-bengioy-ad_cpu,def-bengioy_gpu,def-bengioy_cpu -X -S 2023-03-30T00:00 -E 2023-03-31T00:00 --json


    Here is an example of some fields that could be encountered in a job and some fictitious values
    associated to these fields:
        account = "rrg-cerise-ad_gpu"
        allocation_nodes = 1
        array = {'job_id': 1234, 'limits': {'max': {'running': {'tasks': 0}}}, 'task': None, 'task_id': 0}
        association = {'account': 'rrg-cerise-ad_gpu', 'cluster': 'cedar', 'partition': None, 'user': 'nobody2'}
        cluster = "cedar"
        comment = {'administrator': None, 'job': None, 'system': None}
        constraints = [p100|p100l|v100l]
        derived_exit_code = {'status': 'SUCCESS', 'return_code': 0}
        exit_code = {'status': 'SUCCESS', 'return_code': 0}
        flags = ['CLEAR_SCHEDULING', 'STARTED_ON_BACKFILL']
        group = "nobody2"
        het = {'job_id': 0, 'job_offset': None}
        job_id = 1234
        kill_request_user = None
        mcs = {'label': ''}
        name = "some_name"
        nodes = "cdr2529"
        partition = "part21"
        priority = 1347301
        qos = "normal"
        required = {'CPUs': 4, 'memory': 40960}
        reservation = {'id': 0, 'name': 0}
        state = {'current': 'REQUEUED', 'reason': 'Prolog'}
        steps = []
        time = {'elapsed': 86307, 'eligible': 1680127992, 'end': 1680215981, 'start': 1680127992, 'submission': 1680127990, 'suspended': 0, 'system': {'seconds': 0, 'microseconds': 0}, 'limit': 1440, 'total': {'seconds': 0, 'microseconds': 0}, 'user': {'seconds': 0, 'microseconds': 0}}
        tres = {
            'allocated': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ],
            'requested': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ]
        }
        user = "nobody2"
        wckey = {'wckey': 'some_name', 'flags': []}
        working_directory = "/scratch/nobody2"

    The expected output would then be these associations of keys and values:
        account = "rrg-cerise-ad_gpu"
        array_job_id = "1234"
        array_task_id = "0"
        cluster_name = "cedar"
        exit_code = "SUCCESS:0"
        job_id = "1234"
        name = "some_name"
        nodes = "cdr2529"
        partition = "part21"
        job_state = "REQUEUED"

        # Time parsing
        time_limit = 1440
        submit_time = 1680127990
        start_time = 1680127992
        end_time = 1680215981

        # TRES parsing
        tres_allocated = {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }
        tres_requested = {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }

        username = "nobody2"
        working_directory = "/scratch/nobody2"


    Parameters:
        f       JSON report retrieved from a sacct command

    """
    # Load the JSON file generated by the sacct command
    sacct_data = json.load(f)
    # at this point, sacct_data is a hierarchical structure of dictionaries and lists

    src_jobs = sacct_data["jobs"]  # jobs is a list

    for src_job in src_jobs:
        res_job = (
            dict()
        )  # Initialize the dictionary which will store the newly formatted job data

        for k, v in src_job.items():
            # We will use a handler mapping to translate this
            translator = JOB_FIELD_MAP.get(k, None)

            if translator is not None:
                # Translate using the translator retrieved from JOB_FIELD_MAP
                translator(k, v, res_job)

            # If no translator has been provided: ignore the field

        yield res_job


# The functions used to create the report file, gathering the information to parse


def generate_job_report(
    cluster_name,
    file_name,
):
    """
    Launch a sacct command in order to retrieve a JSON report containing
    jobs information

    Parameters:
        cluster_name    The name of the cluster on which the sinfo command will be launched
        file_name       Path to store the generated sacct report

    """
    # Retrieve from the configuration file the elements used to establish a SSH connection
    # to a remote cluster and launch the sacct command on it
    username = get_config("clusters")[cluster_name][
        "remote_user"
    ]  # The username used for the SSH connection to launch the sacct command
    hostname = get_config("clusters")[cluster_name][
        "remote_hostname"
    ]  # The hostname used for the SSH connection to launch the sacct command
    port = get_config("clusters")[cluster_name][
        "ssh_port"
    ]  # The port used for the SSH connection to launch the sacct command
    sacct_path = get_config("clusters")[cluster_name][
        "sacct_path"
    ]  # The path of the sacct executable on the cluster side
    ssh_key_filename = get_config("clusters")[cluster_name][
        "ssh_key_filename"
    ]  # The name of the private key in .ssh folder used for the SSH connection to launch the sacct command

    # sacct path checks
    assert (
        sacct_path
    ), "Error. We have called the function to make updates with sacct but the sacct_path config is empty."
    assert sacct_path.endswith(
        "sacct"
    ), f"Error. The sacct_path configuration needs to end with 'sacct'. It's currently {sacct_path} ."

    # SSH key check
    assert ssh_key_filename, "Missing ssh_key_filename from config."

    # Now this is the private ssh key that we'll be using with Paramiko.
    ssh_key_path = os.path.join(os.path.expanduser("~"), ".ssh", ssh_key_filename)

    # Note : It doesn't work to simply start the command with "sacct".
    #        For some reason due to paramiko not loading the environment variables,
    #        sacct is not found in the PATH.
    #        This does not work
    #            remote_cmd = "sacct -X -j " + ",".join(L_job_ids)
    #        but if we use
    #            remote_cmd = "/opt/slurm/bin/sacct ..."
    #        then it works. We have to hardcode the path in each cluster, it seems.


    # Retrieve the allocations associated to the cluster
    allocations = get_allocations(cluster_name)

    if allocations == []:
        # If the cluster has no associated allocation, nothing is requested
        print(f"The cluster {cluster_name} has no allocation related to it. Thus, no job has been retrieved. Associated allocations can be provided in the Clockwork configuration file.")
        return []
    else:
        # Set the sacct command
        # -S is a condition on the start time, 600 being in seconds
        # -E is a condition on the end time
        # -X means "Only show statistics relevant to the job allocation itself, not taking steps into consideration."
        # --associations is used in order to limit the fetched jobs to the ones related to Mila and/or professors who
        #                may use Clockwork
        if allocations == "*":
            # We do not provide --associations information because the default for this parameter
            # is "all associations"
            remote_cmd = f"{sacct_path} -S now-600 -E now -X --allusers --json"    
        else:
            accounts_list = ",".join(allocations)
            remote_cmd = f"{sacct_path} -S now-600 -E now -X --accounts={accounts_list} --allusers --json"
        print(f"remote_cmd is\n{remote_cmd}")

        # Connect through SSH
        try:
            ssh_client = open_connection(
                hostname, username, ssh_key_path=ssh_key_path, port=port
            )
        except Exception as inst:
            print(f"Error. Failed to connect to {hostname} to make a call to sacct.")
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
                    f"Stderr in sacct call on {hostname}. This doesn't mean that the call failed entirely, though.\n{response_stderr}"
                )
            """

            # Write the command output to a file
            with open(file_name, "w") as outfile:
                for line in ssh_stdout.readlines():
                    outfile.write(line)

            ssh_client.close()

        else:
            print(
                f"Error. Failed to connect to {hostname} to make call to sacct. Returned `None` but no exception was thrown."
            )
