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


def get_remote_cmd():
    """Get the command to run remotely.
    
    The SSH part will be handled by the parent context,
    but by having `get_remote_cmd` in this file
    we have access to the decision about which fields
    are retrieved.
    """

    accounts = ",".join(get_accounts())
    format = ",".join(get_desired_sacct_fields())
    delimiter = "|"

    cmd = f"sacct --allusers --accounts {accounts} --format {format} --delimiter '{delimiter}' --parsable"
    return cmd


def get_job_desc_from_stdout(stdout:str):
    """Takes the stdout from a remote call and parses it into final result.
    
    This is the function that you want to call from the outside.
    We just need to know what delimiter `sacct` was told to use
    so that we can parse its output from the remote machine.

    TODO : You need to specify the time zone in some way because
           the parsing alone doesn't know if it's coming from British Columbia.
    """
    L_lines = [e for e in stdout.split("\n") if len(e)>0]
 
    delimiter = "|"
    desired_sacct_fields = get_desired_sacct_fields()
    LD_jobs = []
    # skip the header in L_lines[0]
    for line in L_lines[1:]:
        LD_jobs.append( {"raw_sacct" : analyze_stdout_line(desired_sacct_fields, line, delimiter)} )

    for D_job in LD_jobs:
        D_job["sacct"] = process_to_sacct_data(D_job["raw_sacct"])

    return LD_jobs


def process_to_sacct_data(job_raw:dict[str]) -> dict[str]:
    """Takes all the "raw" sacct from Slurm and converts it to cleaner format.
    
    Additionally, it also converts all the CamelCase to more pythonic names.
    """

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


def analyze_stdout_line(sacct_fields, line, delimiter="|"):

    # print(line)

    # Knock off the last delimiter because we want to make it clear
    # that there's no empty string beyond that.
    assert line[-1] == delimiter
    line = line[:-1]

    # Do not reject values with length zero because many will have length zero.
    # L = [e for e in line.split(delimiter) if len(e)>0]
    L = line.split(delimiter)

    if len(L) != len(sacct_fields):
        print(L)
        print(sacct_fields)

    assert len(L) == len(sacct_fields), (f"We have {len(L)} fields read, but we're looking for {len(sacct_fields)} values.")
    return dict(zip(sacct_fields, L))



def get_accounts():
    """Returns the CC allocations that are relevant to Mila.
    """
    return [# greater Yoshua account for many people
            'def-bengioy_gpu', 'rrg-bengioy-ad_gpu', 'rrg-bengioy-ad_cpu', 'def-bengioy_cpu',
            # doina + joelle + jackie
            'rrg-dprecup', 'def-dprecup',
            # blake williams
            'def-tyrell', 'rrg-tyrell', 'rpp-markpb68']


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
    field_names = [field_name for field_name in raw_str.split(" ") if len(field_name)>0]
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
    field_names = [field_name for field_name in raw_str.split(" ") if len(field_name)>0]
    return field_names

