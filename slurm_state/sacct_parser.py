"""
The sacct parser is used to convert jobs retrieved through a sacct command on a cluster
to jobs in the format used by Clockwork.
"""
import json, os
from slurm_state.helpers.parser_helper import copy, ignore, rename

# Imports related to sacct call
# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy, ssh_exception

from slurm_state.extra_filters import clusters_valid
from slurm_state.config import get_config, string, optional_string, timezone
clusters_valid.add_field("sacct_path", optional_string)
clusters_valid.add_field("sacct_ssh_key_filename", string)
clusters_valid.add_field("timezone", timezone)
clusters_valid.add_field("remote_user", optional_string)
clusters_valid.add_field("remote_hostname", optional_string)

# These functions are translators used in order to handle the values
# we could encounter while parsing a job dictionary retrieved from a
# sacct command.
#
# The following functions are only used by the job parser. Translator
# functions shared with the node parser are store retrieved from
# slurm_state.helpers.parser_helper.


def copy_and_stringify(k, v, res):
    res[k] = str(v)


def rename_subitems(subitem_dict):
    def renamer(k, v, res):
        for subitem, name in subitem_dict.items():
            res[name] = v[subitem]

    return renamer


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
# and set the result in the output dictionary. You can ignore fields, by
# assigning them to 'ignore'

JOB_FIELD_MAP = {
    "account": copy,
    "allocation_nodes": ignore,
    "array": rename_and_stringify_subitems(
        {"job_id": "array_job_id", "task_id": "array_task_id"}
    ),
    "association": ignore,
    "cluster": rename("cluster_name"),
    "comment": ignore,
    "container": ignore,
    "constraints": ignore,
    "derived_exit_code": ignore,
    "exit_code": join_subitems(":", "exit_code"),
    "flags": ignore,
    "group": ignore,
    "het": ignore,
    "job_id": copy_and_stringify,
    "kill_request_user": ignore,
    "mcs": ignore,
    "name": copy,
    "nodes": copy,
    "partition": copy,
    "priority": ignore,
    "qos": ignore,
    "required": ignore,
    "reservation": ignore,
    "state": rename_subitems({"current": "job_state"}),
    "steps": ignore,
    "time": rename_subitems(
        {
            "limit": "time_limit",
            "submission": "submit_time",
            "start": "start_time",
            "end": "end_time",
        }
    ),
    "tres": extract_tres_data,
    "user": rename("username"),
    "wckey": ignore,
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

def generate_job_report(cluster_name, file_name, username=None, hostname=None, port=None, sacct_path=None, sacct_ssh_key_filename=None):
    """
    Launch a sacct command in order to retrieve a JSON report containing
    jobs information 

    Parameters:
        file_name   Path to store the generated sacct report
    
    """
    # these fields are already present in the config because
    # they are required in order to rsync the scontrol reports
    username = get_config("clusters")[cluster_name]["remote_user"]
    hostname = get_config("clusters")[cluster_name]["remote_hostname"]
    sacct_path = get_config("clusters")[cluster_name]["sacct_path"]
    sacct_ssh_key_filename = get_config("clusters")[cluster_name][
        "sacct_ssh_key_filename"
    ]
    assert (
        sacct_path
    ), "Error. We have called the function to make updates with sacct but the sacct_path config is empty."
    assert sacct_path.endswith(
        "sacct"
    ), f"Error. The sacct_path configuration needs to end with 'sacct'. It's currently {sacct_path} ."
    assert sacct_ssh_key_filename, "Missing sacct_ssh_key_filename from config."
    # Now this is the private ssh key that we'll be using with Paramiko.
    sacct_ssh_key_path = os.path.join(
        os.path.expanduser("~"), ".ssh", sacct_ssh_key_filename
    )

    # If you need to change this value in any way, then you should
    # make it a config value for real. In the meantime, let's hardcode it.
    port = 22

    # Note : It doesn't work to simply start the command with "sacct".
    #        For some reason due to paramiko not loading the environment variables,
    #        sacct is not found in the PATH.
    #        This does not work
    #            remote_cmd = "sacct -X -j " + ",".join(L_job_ids)
    #        but if we use
    #            remote_cmd = "/opt/slurm/bin/sacct ..."
    #        then it works. We have to hardcode the path in each cluster, it seems.

    # Retrieve only certain fields.
    remote_cmd = (
        f"{sacct_path} -X --json"
    )

    print(f"remote_cmd is\n{remote_cmd}")
    
    # Connect through SSH
    try:
        ssh_client = open_connection(
            hostname, username, ssh_key_path=sacct_ssh_key_path, port=port
        )
    except Exception as inst:
        print(f"Error. Failed to connect to {hostname} to make a call to sacct.")
        print(inst)
        return []

    if ssh_client:
        # those three variables are file-like, not strings
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(remote_cmd)

        response_stderr = "\n".join(ssh_stderr.readlines())
        if len(response_stderr):
            print(
                f"Stderr in sacct call on {hostname}. This doesn't mean that the call failed entirely, though.\n{response_stderr}"
            )

        print("STDOUT")
        print(ssh_stdout)

        ssh_client.close()
    else:
        print(
            f"Error. Failed to connect to {hostname} to make call to sacct. Returned `None` but no exception was thrown."
        )


def open_connection(hostname, username, ssh_key_path, port=22):
    """
    If successful, this will connect to the remote server and
    the value of self.ssh_client will be usable.
    Otherwise, this will set self.ssh_client=None or it will quit().
    """

    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.load_system_host_keys()
    assert os.path.exists(
        ssh_key_path
    ), f"Error. The absolute path given for ssh_key_path does not exist: {ssh_key_path} ."

    # The call to .connect was seen to raise an exception now and then.
    #     raise AuthenticationException("Authentication timeout.")
    #     paramiko.ssh_exception.AuthenticationException: Authentication timeout.
    # When it happens, we should simply give up on the attempt
    # and log the error to stdout.
    try:
        # For some reason, we really need to specify which key_filename to use.
        ssh_client.connect(
            hostname, username=username, port=port, key_filename=ssh_key_path
        )
        print(f"Successful SSH connection to {username}@{hostname} port {port}.")
    except ssh_exception.AuthenticationException as inst:
        print(f"Error in SSH connection to {username}@{hostname} port {port}.")
        print(type(inst))
        print(inst)
        # set the ssh_client to None as a way to communicate
        # to the parent that we got into trouble
        ssh_client = None
    except Exception as inst:
        print(f"Error in SSH connection to {username}@{hostname} port {port}.")
        print(type(inst))
        print(inst)
        ssh_client = None

    return ssh_client