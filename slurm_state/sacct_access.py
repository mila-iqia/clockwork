"""

For inspiration about the way to connect by SSH,
see the code that dates from before the first major refactoring.

https://github.com/mila-iqia/clockwork/blob/refactor/slurm_monitor/on_site_sinfo_and_sacct_scraper.py
https://github.com/mila-iqia/clockwork/blob/refactor/slurm_monitor/main.py


alaingui@login-2:~$ sacct -X -j 2330417,2331586
     User        JobID    JobName  Partition      State  Timelimit               Start                 End    Elapsed   NNodes      NCPUS     ReqMem  AllocTRES        NodeList              WorkDir 
--------- ------------ ---------- ---------- ---------- ---------- ------------------- ------------------- ---------- -------- ---------- ---------- ---------- --------------- -------------------- 
goncalo-+ 2330417      train_cif+ unkillable  COMPLETED 2-00:00:00 2022-10-06T08:36:14 2022-10-06T12:14:16   03:38:02        1          1       32Gn cpu=1,gre+         cn-a001 /home/mila/g/goncal+ 
ximeng.m+ 2331586      submit_jo+   cpu_jobs  COMPLETED 3-08:00:00 2022-10-03T10:05:39 2022-10-05T20:06:13 2-10:00:34        1          1       16Gn billing=3+         cn-f004 /home/mila/x/ximeng+ 
alaingui@login-2:~$ sacct -X --format 'Account,UID,User,JobID,JobName,State,Start,End,ReqTRES' --delimiter '|' --parsable -j 2330417,2331586
Account|UID|User|JobID|JobName|State|Start|End|ReqTRES|
mila|720391130|goncalo-filipe.torcato-mordido|2330417|train_cifar.sh|COMPLETED|2022-10-06T08:36:14|2022-10-06T12:14:16|cpu=1,gres/gpu=1,mem=32G,node=1|
mila|2054761827|ximeng.mao|2331586|submit_job_multi_kfold_cpu.sh|COMPLETED|2022-10-03T10:05:39|2022-10-05T20:06:13|billing=3,cpu=1,mem=16G,node=1|

Note that we'll never account for jobs that ended up in the database in a weird non-terminal state
and are not currently visible with sacct.

We also have some intricate manipulations that we can do in order to process the jobs that
we know for a fact would be relevant, but for some reason have been missed completely by scontrol_show_job.
See https://mila-iqia.atlassian.net/browse/CW-213 for more discussion.

"""

import csv  # sacct output reads like a csv
import re
import os

# from io import StringIO

# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy, ssh_exception

from slurm_state.extra_filters import clusters_valid
from slurm_state.config import get_config, string, optional_string
from slurm_state.scontrol_parser import timestamp as parse_timestamp

clusters_valid.add_field("sacct_path", optional_string)
clusters_valid.add_field("sacct_ssh_key_filename", string)


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
        # TODO : Use some kind of config instead of writing that path there.
        #        Strangely, this doesn't work unless we specify that path.
        #        Maybe it's the unconventional naming scheme.
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


def fetch_data_with_sacct_on_remote_clusters(cluster_name: str, L_job_ids: list[str], timezone:str):
    """
    Fetches through SSH certain fields for jobs that have
    been dropped from scontrol_show_job prematurely before
    their final JobState was captured.
    Basically, we want to refrain from large queries
    to respect Compute Canada's wishes so we limit ourselves
    to one such query per job (in the entire lifecycle of the job)
    and we only retrieve fields that could have been updated
    during the life of the job (i.e. after it was first seen
    in scontrol_show_job).

    The intended use for this involves only jobs with a perceived
    `job_state` of "RUNNING" or "PENDING" in our MongoDB database.

    Returns a list of dict of the form
    {
        "job_id" : ...,
        "job_state" : ...,
        "start_time" : ...,
        "end_time" : ...,
        "submit_time" : ...,
        "exit_code" : ...
    }
    """

    if len(L_job_ids) == 0:
        print(
            f"Error. You called for an update with remote sacct on {cluster_name}, but the supplied argument L_job_ids is empty."
        )
        return

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
        f"{sacct_path} -X --format Account,UID,User,JobIDRaw,JobID,JobName,State,Submit,Start,End --delimiter '|' --parsable -j "
        + ",".join(L_job_ids)
    )

    print(f"remote_cmd is\n{remote_cmd}")

    # Write what keys you want to map to what, because we use a different representation for ourselves.
    key_mappings = {
        "Account": "account",
        "UID": "uid",
        "User": "username",
        "JobIDRaw": "job_id",
        # We have "JobID" in the query, but we don't map it automatically to something
        # because it can be of the form : array_job_id + underscore + array_task_id.
        # We handle this manually down below.
        "JobName": "name",
        "State": "job_state",
        "Submit": "submit_time",
        "Start": "start_time",
        "End": "end_time",
    }

    # for faster lookups
    S_job_ids = set(L_job_ids)

    LD_partial_slurm_jobs = []

    ssh_client = open_connection(
        hostname, username, ssh_key_path=sacct_ssh_key_path, port=port
    )
    if ssh_client:

        # those three variables are file-like, not strings
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(remote_cmd)

        reader = csv.DictReader(ssh_stdout, delimiter="|")
        for row in reader:
            # this is just a dict with the proper keys that we specified,
            # e.g. to have "job_state" instead of "JobState"
            D_partial_slurm_job = dict(
                (k2, row[k1]) for (k1, k2) in key_mappings.items()
            )

            # We need to properly handle times to translate them to unix format
            # like we do in scontrol_parser. Reuse that code. The `timezone` is
            # because certain clusters are not in the same time zone as us.
            for k in ["submit_time", "start_time", "end_time"]:
                D_partial_slurm_job[k] = parse_timestamp(D_partial_slurm_job[k], {"timezone": timezone})

            if row["JobID"] == row["JobIDRaw"]:
                # not part of an array, so we don't return values for
                # "array_job_id" or "array_task_id"
                pass
            else:
                # According to the Slurm documentation (https://slurm.schedmd.com/job_array.html),
                # this should be of the form SLURM_ARRAY_JOB_ID plus SLURM_ARRAY_TASK_ID.
                m = re.match(r"^(\d+)_(.*)$", row["JobID"])
                if m:
                    D_partial_slurm_job["array_job_id"] = m.group(1)
                    D_partial_slurm_job["array_task_id"] = m.group(2)
                else:
                    print(
                        "Error. We've indentified a situation where all our expectations are broken.\n"
                        "We have a situation where we suspected that we had an array job id plus array task id situation but we cannot parse it properly."
                        f'(row["JobID"], row["JobIDRaw"]) is ({row["JobID"]}, {row["JobIDRaw"]})'
                    )

            # Cancelled jobs can have a JobState in the form "CANCELLED by 963245100".
            # We don't want to have that. It would be possible to argue
            # that we're throwing away good information by doing this,
            # but this wouldn't be the first place where we make an informed decision
            # about what to keep and what to remove.
            if D_partial_slurm_job["job_state"].startswith("CANCELLED"):
                D_partial_slurm_job["job_state"] = "CANCELLED"

            # Note while we expect generally that
            #     D_partial_slurm_job["job_id"] in S_job_ids
            # it's very possible that such won't be the case
            # when dealing with job arrays.

            LD_partial_slurm_jobs.append(D_partial_slurm_job)

        response_stderr = "\n".join(ssh_stderr.readlines())
        if len(response_stderr):
            print(
                f"Error when trying to remotely call sacct on {hostname}.\n{response_stderr}"
            )
            return
        ssh_client.close()

    return LD_partial_slurm_jobs
