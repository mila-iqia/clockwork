"""
Design decision - Jobs entries are going to have three subdicts.

    job["sacct"] : the stuff that we translated from CamelCase and massaged
    job["raw_sacct"] : the original stuff that we got from Slurm sacct with CamelCase
    job["cw"] : the properties relevant to clockwork, which includes later properties that the owner can set

The reason for that it that it quickly becomes a mess of fields that
are overridden with fields that are added, and then it's hard for the user
to know what's coming from where.

In this way, we'll provide a convenient format for them without erasing
some of the raw fields that they might have wanted to use. This goes with
the idea of trusting them to be programmers who can dig deep in they want.

Note that we keep track of the fact that it's coming from "sacct"
when we say "raw_sacct" because of the possibility later to go back to PySlurm.
"""

from __future__ import annotations

from pprint import pprint
import re
import subprocess
import json

import datetime
import time

# Note about delimiters:
#   Don't use "|" because sacct can return things like
#   "x86_64&(32gb|48gb)" which will get split into two terms.
#
# Let's pick something that won't occur accidentally.

delimiter = "<^>"


def get_remote_sacct_cmd():
    """Get the command to run remotely.

    The SSH part will be handled by the parent context,
    but by having `get_remote_sacct_cmd` in this file
    we have access to the decision about which fields
    are retrieved.
    """

    accounts = ",".join(get_accounts())
    format = ",".join(get_desired_sacct_fields())
    # delimiter =

    cmd = f"sacct --allusers --accounts {accounts} --format {format} --delimiter '{delimiter}' --parsable"
    return cmd


def get_jobs_desc_from_stdout(stdout: str, cluster_desc: dict):
    """Takes the stdout from a remote call and parses it into final result.

    This is the function that you want to call from the outside.
    We just need to know what delimiter `sacct` was told to use
    so that we can parse its output from the remote machine.

    The `cluster_desc` is needed for things such as interpreting the
    times properly or user names.

    Args:
        stdout (str) : The output of the sacct command.
        cluster_desc (dict) : The description of the cluster coming from
        the parent script, needed for decisions about how to interpret the data.

    Returns:
        list[dict]: List of descriptions for each individual jobs.
    """
    L_lines = [e for e in stdout.split("\n") if len(e) > 0]

    # delimiter =
    desired_sacct_fields = get_desired_sacct_fields()
    LD_jobs = []
    # skip the header in L_lines[0]
    for line in L_lines[1:]:
        LD_jobs.append(
            {"raw_sacct": analyze_stdout_line(desired_sacct_fields, line, delimiter)}
        )

    for D_job in LD_jobs:
        D_job["sacct"] = process_to_sacct_data(D_job["raw_sacct"], cluster_desc)

    return LD_jobs


def process_to_sacct_data(job_raw_sacct: dict[str], cluster_desc: dict) -> dict[str]:
    """Takes all the "raw" sacct from Slurm and converts it to cleaner format.

    Additionally, it converts all the CamelCase to more pythonic names.
    It also converts the times from their original locations into unix timestamps.
    This requires the "timezone_offset_montreal_minus_there_in_seconds"
    from the cluster_desc.
    """

    job_sacct = {}

    job_sacct["account"] = job_raw_sacct["Account"]
    job_sacct["alloc_node"] = job_raw_sacct["AllocNodes"]
    job_sacct["tres_req_str"] = job_raw_sacct[
        "ReqTRES"
    ]  # why the str? are we syncing with pyslurm with that?
    job_sacct["tres_alloc_str"] = job_raw_sacct[
        "AllocTRES"
    ]  # why the str? are we syncing with pyslurm with that?
    job_sacct["work_dir"] = job_raw_sacct["WorkDir"]

    # unsure about this mapping
    job_sacct["user_id"] = job_raw_sacct["UID"]

    # Depending which cluster where we find this username,
    # we'll put it in a different slot. This is important
    # to distinguish with the (currently) three identities we track.
    job_sacct[cluster_desc["local_username_referenced_by_parent_as"]] = job_raw_sacct[
        "User"
    ]

    job_sacct["job_state"] = job_raw_sacct["State"]
    job_sacct["partition"] = job_raw_sacct["Partition"]

    ##################################################################
    #
    #   Stuff after here starts being a bit shady.
    #
    #   Some arbitrary decisions are weird if you don't take into
    #   consideration a desire to harmonize with whatever PySlurm
    #   was returning. This is not a nice thing.
    #   We should discuss this design at some point.
    ##################################################################

    # You might think that JobID should be an integer, but it gets
    # values like '3114459_1.batch' so it's not an integer.
    job_sacct["job_id"] = job_raw_sacct["JobID"]
    job_sacct["job_id_raw"] = job_raw_sacct["JobIDRaw"]

    # This one is an editorial decision. These look similar
    # but it's dangerous to some degree to start matching
    # fields that aren't necessarily the same.
    job_sacct["command"] = job_raw_sacct["JobName"]

    # Nope. One is a list and the other is an integer written as string.
    # job_sacct['req_nodes'] = job_raw_sacct['ReqNodes']

    job_sacct["resv_name"] = (
        job_raw_sacct["Reservation"] if 0 < len(job_raw_sacct["Reservation"]) else None
    )

    """
    job_raw_sacct['Submit'] is something like 2021-05-08T15:37:35
    job_raw_sacct['Start'], job_raw_sacct['End'] can be "Unknown"
    job_raw_sacct['Eligible'] is something like 2021-05-08T15:37:35

    D_job['submit_time'] is unix time as integer.
    Same for 'submit_time', 'start_time', 'end_time', 'eligible_time'.

    Remember that cedar is in Vancouver time.
    """

    #### Submit ####
    job_sacct["submit_time"] = int(localtime_to_unix_timestamp(job_raw_sacct["Submit"]))
    #### Start ####
    if job_raw_sacct["Start"] is None or job_raw_sacct["Start"] == "Unknown":
        job_sacct["start_time"] = None
    else:
        job_sacct["start_time"] = int(
            localtime_to_unix_timestamp(job_raw_sacct["Start"])
        )
    #### End ####
    if job_raw_sacct["End"] is None or job_raw_sacct["End"] == "Unknown":
        job_sacct["end_time"] = None
    else:
        job_sacct["end_time"] = int(localtime_to_unix_timestamp(job_raw_sacct["End"]))
    #### Eligible ####
    job_sacct["eligible_time"] = int(
        localtime_to_unix_timestamp(job_raw_sacct["Eligible"])
    )
    ####

    # No idea what this does, but the mapping seems natural.
    job_sacct["assoc_id"] = int(job_raw_sacct["AssocID"])

    """
        "time_limit": 900,
        "time_limit_str": "15:00:00",
        "Timelimit": "23:59:00",
        "TimelimitRaw": "1439",
    """
    job_sacct["time_limit"] = (
        int(job_raw_sacct["TimelimitRaw"]) if job_raw_sacct["TimelimitRaw"] else 0
    )
    job_sacct["time_limit_str"] = job_raw_sacct["Timelimit"]

    job_sacct["exit_code"] = job_raw_sacct["ExitCode"]

    # You are not done here. Continue from "on_site_sinfo_and_sacct_scraper.py".

    # TODO : Code this.
    #        It involves a lot of the real meat with certain
    #        key decisions about how to convert the fields.
    return {}


# def process_to_cw_data(job_raw:dict[str], job_sacct:dict[str]) -> dict[str]:
#     """Obtains the "cw" field for job descriptions.
#
#     """
#     return {}


#####################################################
#                                                   #
#  The rest of this file is just helper functions.  #
#                                                   #
#####################################################


def analyze_stdout_line(sacct_fields, line, delimiter):
    """ """

    # The problem is that sometimes we have one more delimiter at the end,
    # despite having no elements after. It doesn't appear to be consistent
    # between every platform (and between sacct/sinfo on the same platform).
    # We'll split the lines anyways and consume the tokens if we have exactly
    # the right number, or that number+1.

    # Do not reject values with length zero because many will have length zero.
    L = line.split(delimiter)

    if len(L) == len(sacct_fields):
        return dict(zip(sacct_fields, L))
    elif len(L) == len(sacct_fields) + 1:
        # if we're off by one in the number of tokens, at least check
        # that the last one is just zero of more empty spaces
        assert re.match(r"\s*", L[-1])
        return dict(zip(sacct_fields, L[:-1]))  # dropping the last one
    else:
        print("-----------")
        print(line)
        print(L)
        print(sacct_fields)
        print("-----------")
        raise Exception(
            f"We have {len(L)} fields read, but we're looking for {len(sacct_fields)} values."
        )


def get_accounts():
    """Returns the CC allocations that are relevant to Mila."""
    return [  # we need 'mila' in there now that we run this method instead of PySlurm at Mila
        "mila",
        # greater Yoshua account for many people
        "def-bengioy_gpu",
        "rrg-bengioy-ad_gpu",
        "rrg-bengioy-ad_cpu",
        "def-bengioy_cpu",
        # doina + joelle + jackie
        "rrg-dprecup",
        "def-dprecup",
        # blake williams
        "def-tyrell",
        "rrg-tyrell",
        "rpp-markpb68",
    ]


def get_valid_sacct_fields():
    """
    Returns all the field names that `sacct` will accept. This is a sanity check
    to avoid typos.
    """
    raw_str = """
        Account             AdminComment        AllocCPUS           AllocNodes
        AllocTRES           AssocID             AveCPU              AveCPUFreq
        AveDiskRead         AveDiskWrite        AvePages            AveRSS
        AveVMSize           BlockID             Cluster             Comment
        Constraints         ConsumedEnergy      ConsumedEnergyRaw   CPUTime
        CPUTimeRAW          DBIndex             DerivedExitCode     Elapsed
        ElapsedRaw          Eligible            End                 ExitCode
        Flags               GID                 Group               JobID
        JobIDRaw            JobName             Layout              MaxDiskRead
        MaxDiskReadNode     MaxDiskReadTask     MaxDiskWrite        MaxDiskWriteNode
        MaxDiskWriteTask    MaxPages            MaxPagesNode        MaxPagesTask
        MaxRSS              MaxRSSNode          MaxRSSTask          MaxVMSize
        MaxVMSizeNode       MaxVMSizeTask       McsLabel            MinCPU
        MinCPUNode          MinCPUTask          NCPUS               NNodes
        NodeList            NTasks              Priority            Partition
        QOS                 QOSRAW              Reason              ReqCPUFreq
        ReqCPUFreqMin       ReqCPUFreqMax       ReqCPUFreqGov       ReqCPUS
        ReqMem              ReqNodes            ReqTRES             Reservation
        ReservationId       Reserved            ResvCPU             ResvCPURAW
        Start               State               Submit              Suspended
        SystemCPU           SystemComment       Timelimit           TimelimitRaw
        TotalCPU            TRESUsageInAve      TRESUsageInMax      TRESUsageInMaxNode
        TRESUsageInMaxTask  TRESUsageInMin      TRESUsageInMinNode  TRESUsageInMinTask
        TRESUsageInTot      TRESUsageOutAve     TRESUsageOutMax     TRESUsageOutMaxNode
        TRESUsageOutMaxTask TRESUsageOutMin     TRESUsageOutMinNode TRESUsageOutMinTask
        TRESUsageOutTot     UID                 User                UserCPU
        WCKey               WCKeyID             WorkDir
    """
    raw_str = raw_str.replace("\n", " ")
    field_names = [
        field_name for field_name in raw_str.split(" ") if len(field_name) > 0
    ]
    return field_names


# map_camel_to_underscore = {
#     "Account": "account",
#     "AdminComment": "admin_comment",
#     "AllocCPUS": "alloc_cpus",
#                              AllocCPUS           AllocNodes
#         AllocTRES           AssocID             AveCPU              AveCPUFreq
#         AveDiskRead         AveDiskWrite        AvePages            AveRSS
#         AveVMSize           BlockID             Cluster             Comment
#         Constraints         ConsumedEnergy      ConsumedEnergyRaw   CPUTime
#         CPUTimeRAW          DBIndex             DerivedExitCode     Elapsed
#         ElapsedRaw          Eligible            End                 ExitCode
#         Flags               GID                 Group               JobID
#         JobIDRaw            JobName             Layout              MaxDiskRead
#         MaxDiskReadNode     MaxDiskReadTask     MaxDiskWrite        MaxDiskWriteNode
#         MaxDiskWriteTask    MaxPages            MaxPagesNode        MaxPagesTask
#         MaxRSS              MaxRSSNode          MaxRSSTask          MaxVMSize
#         MaxVMSizeNode       MaxVMSizeTask       McsLabel            MinCPU
#         MinCPUNode          MinCPUTask          NCPUS               NNodes
#         NodeList            NTasks              Priority            Partition
#         QOS                 QOSRAW              Reason              ReqCPUFreq
#         ReqCPUFreqMin       ReqCPUFreqMax       ReqCPUFreqGov       ReqCPUS
#         ReqMem              ReqNodes            ReqTRES             Reservation
#         ReservationId       Reserved            ResvCPU             ResvCPURAW
#         Start               State               Submit              Suspended
#         SystemCPU           SystemComment       Timelimit           TimelimitRaw
#         TotalCPU            TRESUsageInAve      TRESUsageInMax      TRESUsageInMaxNode
#         TRESUsageInMaxTask  TRESUsageInMin      TRESUsageInMinNode  TRESUsageInMinTask
#         TRESUsageInTot      TRESUsageOutAve     TRESUsageOutMax     TRESUsageOutMaxNode
#         TRESUsageOutMaxTask TRESUsageOutMin     TRESUsageOutMinNode TRESUsageOutMinTask
#         TRESUsageOutTot     UID                 User                UserCPU
#         WCKey               WCKeyID             WorkDir

# }


# A while ago, there were good reasons to avoid retrieving all the fields
# since most of them did not correspond to something in PySlurm,
# and PySlurm was the standard that we were trying to match.
# Now that PySlurm is no longer the reference, we'll just get everything
# that sacct has to give us.
get_desired_sacct_fields = get_valid_sacct_fields


def get_desired_sacct_fields_00():
    """
    This is a subset of the `sacct` fields that we're interested in.

    OBSOLETE, but might be useful to keep around.
    """

    raw_str = """
        Account             AdminComment        AllocCPUS           AllocNodes
        AllocTRES           AssocID  

        JobID JobIDRaw JobName
        End Start
        State
        Submit              Suspended
        Timelimit
        TimelimitRaw
        Elapsed
        ElapsedRaw          Eligible

        ExitCode
        NNodes
        NodeList
        Partition

        ReqNodes            ReqTRES             Reservation
        ReservationId       Reserved

        UID
        User                UserCPU
            WorkDir
       """
    raw_str = raw_str.replace("\n", " ")
    field_names = [
        field_name for field_name in raw_str.split(" ") if len(field_name) > 0
    ]
    return field_names
