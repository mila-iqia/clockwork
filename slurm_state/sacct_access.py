
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

"""


# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy, ssh_exception

from slurm_state.extra_filters import clusters_valid
from slurm_state.config import get_config, string

clusters_valid.add_field("sacct_username", string)
clusters_valid.add_field("sacct_remote_hostname", string)


def open_connection(hostname, username, port=22):
    """
    If successful, this will connect to the remote server and
    the value of self.ssh_client will be usable.
    Otherwise, this will set self.ssh_client=None or it will quit().
    """

    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.load_system_host_keys()

    # The call to .connect was seen to raise an exception now and then.
    #     raise AuthenticationException("Authentication timeout.")
    #     paramiko.ssh_exception.AuthenticationException: Authentication timeout.
    # When it happens, we should simply give up on the attempt
    # and log the error to stdout.
    try:        
        ssh_client.connect(hostname, username=username, port=port)
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


def bleh(cluster_name, L_job_ids):

    if len(L_job_ids) == 0:
        print(f"Error. You called for an update with remote sacct on {cluster_name}, but the supplied argument L_job_ids is empty.")
        return

    username = get_config("clusters")[cluster_name]["sacct_username"]
    hostname = get_config("clusters")[cluster_name]["sacct_remote_hostname"]
    port = get_config("clusters")[cluster_name].get("port", 22)

    #remote_cmd = "sacct -X -j " + ",".join(L_job_ids)

    remote_cmd = "sacct -X --format 'Account,UID,User,JobID,JobName,State,Start,End' --delimiter '|' --parsable -j " + ",".join(L_job_ids)
    # TODO : list the keys yourself so that they match with that you have in D_job entries
    value_keys = ["account,uid,username,job_id,name,job_state,start_time,end_time"]


    with open_connection(hostname, username, port) as ssh_client:

        if ssh_client:

            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(remote_cmd)

            response_str = " ".join(ssh_stdout.readlines())
            if len(response_str) == 0:
                print(f"Error. Got an empty response when trying to call sacct through SSH on {hostname}. Skipping.")
                return


        # we get the ssh_client.close() for free


def fetch_data_with_sacct_on_remote_clusters(cluster_name, L_job_ids):
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
    return []
