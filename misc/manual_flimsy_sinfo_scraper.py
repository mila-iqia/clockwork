
from pprint import pprint
import re
import subprocess
import json


def translate_into_pyslurm_format(D_results):

    D_job = {}

    D_job['account'] = D_results['Account']
    
    D_job['tres_req_str'] = D_results['ReqTRES']
    D_job['tres_alloc_str'] = D_results['AllocTRES']

    D_job['work_dir'] = D_results['WorkDir']

    # unsure about this mapping
    D_job['user_id'] = int(D_results['UID'])

    # maybe call it "username" ?
    D_job['mila_account_user'] = D_results['User']

    D_job['job_state'] = D_results['State']
    D_job['partition'] = D_results['Partition']

    # this is a bit strange because sometimes we have a 'JobIdRaw' that doesn't match
    D_job['job_id'] = int(D_results['JobId'])

    # This one is an editorial decision. These look similar
    # but it's dangerous to some degree to start matching
    # fields that aren't necessarily the same.
    D_job['command'] = D_results['JobName']

    # Nope. One is a list and the other is an integer written as string.
    # D_job['req_nodes'] = D_results['ReqNodes']

    D_job['resv_name'] = D_results['Reservation'] if 0<len(D_results['Reservation']) else None


    """
    D_results['Submit'] is something like 2021-05-08T15:37:35
    D_results['Start'], D_results['End'] can be "Unknown"
    D_results['Eligible'] is something like 2021-05-08T15:37:35

    D_job['submit_time'] is unix time as integer.
    Same for 'submit_time', 'start_time', 'end_time', 'eligible_time'.

    Remember that cedar is in Vancouver time.
    You will do the conversion on the server side anyways, so this
    should be fine.
    """

    # No idea what this does, but the mapping seems natural.
    D_job['assoc_id'] = int(D_results['AssocID'])

    """
        "time_limit": 900,
        "time_limit_str": "15:00:00",
        "Timelimit": "23:59:00",
        "TimelimitRaw": "1439",
    """
    D_job['time_limit'] = int(D_results['TimelimitRaw'])
    D_job['time_limit_str'] = D_results['Timelimit']

    D_job['exit_code'] = D_results['ExitCode']

    # Something like that could be done.
    #     D_job['nodes'] = D_results['NodeList']
    #
    # However, this needs some care because we need to know the representation used
    # when facing many nodes in an enumeration. We should assume that it's going to
    # be something like blg[4109,5608-5609,5803-5804] which we're not going to parse.
    # 
    # At the current time, we're only doing the expansion when it comes to "reservations"
    # so that end up being somewhat useless, unfortunately.
    # We have a TODO element in README.md for that, called "add_node_list_simplified on the wrong data structure!".
    #
    # The point is that more could and should be done to have this
    # be a proper list of node names and never a shorthand that only
    # slurm knows how to parse.
    if D_results['NodeList'] == "None assigned":
        D_job['nodes'] = None
    else:
        D_job['nodes'] = D_results['NodeList']

    # Note that there might be other fields that we're leaving out at the moment.

    return D_job


def get_accounts():
    return ['def-bengioy_gpu', 'rrg-bengioy-ad_gpu', 'rrg-bengioy-ad_cpu', 'def-bengioy_cpu']

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


def get_desired_sacct_fields():
    """
    This is a subset of the `sacct` fields that we're interested in.
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



def main():
    valid_sacct_fields = get_valid_sacct_fields()
    # print(valid_sacct_fields)

    desired_sacct_fields = get_desired_sacct_fields()

    accounts = ",".join(get_accounts())
    format = ",".join(desired_sacct_fields) #[e.lower() for e in valid_sacct_fields])
    delimiter = "|"

    cmd = f"sacct --allusers --accounts {accounts} --format {format} --delimiter '{delimiter}' --parsable"
    # print(cmd)


    # pprint(analyze_stdout_line(get_desired_sacct_fields(), get_sample_response_00()))
    # pprint(analyze_stdout_line(get_desired_sacct_fields(), get_sample_response_01()))

    L_lines = [e for e in subprocess.check_output(cmd, shell=True, encoding='utf8').split("\n") if len(e)>0]
 
    LD_jobs = []
    # skip the header in L_lines[0]
    for line in L_lines[1:]:
        LD_jobs.append( analyze_stdout_line(desired_sacct_fields, line, delimiter) )

    # with open("sinfo_LD_jobs.json", "w") as f:
    #     json.dump(LD_jobs, f)
    # pprint(json.dumps(LD_jobs))

    results = { 'node': {},
                'reservation': {},
                'job': [translate_into_pyslurm_format(D_job) for D_job in LD_jobs]}

    # We print results because the parent script will retrieve them as stdout.
    print(json.dumps(results))

    # YOU ARE HERE.
    #     test this
    #     deploy
    #     maybe add stuff for nodes?
    #     probably not stuff for reservations


if __name__ == "__main__":
    main()

"""
    rsync -av ${HOME}/Documents/code/slurm_monitoring_and_reporting/misc/manual_flimsy_sinfo_scraper.py cedar:bin


    rsync -av cedar:Documents/sinfo_LD_results.json ${HOME}/Documents/code/slurm_monitoring_and_reporting/misc
"""