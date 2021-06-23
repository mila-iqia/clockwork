"""
Because pyslurm does not run on `cedar`, we need to have some kind of substitute.
We use this script instead, with a silly name that indicate its hacky/temporary nature.

It tries to provide the kind of information that pyslurm.job().get() provides,
but that's it. No attempt at `pyslurm.node().get()`.
"""

from pprint import pprint
import re
import subprocess
import json

import datetime
import time





#### functions for `sacct` ####


def date_sanity_check():
    """
    Yes, this should probably be removed from the final version.
    """
    dt = datetime.datetime.now()
    # datetime is naive
    assert dt.tzinfo is None

    dt = dt.astimezone()
    assert dt.tzinfo is not None

    # this should be very very close
    assert -1 < dt.timestamp() - time.time() < 1

    # datetime.fromtimestamp(dt.timestamp())
    # datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


def localtime_to_unix_timestamp(date_string:str):
    """
    We need to convert time expressed in local time string as "2021-05-08T15:37:35"
    into unix time that's not dependent on time zone.
    This is needed because the Cedar cluster is in Vancouver
    and we don't want a tangle of badly-synced timestamps.

    date_string = "2021-05-08T15:37:35"
    """

    # date is naive
    date_naive = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    # add the time zone from the system
    date_aware = date_naive.astimezone()

    return date_aware.timestamp()


def translate_sacct_format_into_pyslurm_format(D_results):
    """
    Because we are not getting the same rich information as we get through pyslurm,
    we have to do some manual translation. We are not going to try to integrate
    everything, but rather only the fields that have their obvious equivalents.
    """

    D_job = {}

    D_job['account'] = D_results['Account']

    D_job['alloc_node'] = D_results['AllocNodes']

    D_job['tres_req_str'] = D_results['ReqTRES']
    D_job['tres_alloc_str'] = D_results['AllocTRES']

    D_job['work_dir'] = D_results['WorkDir']

    # unsure about this mapping
    D_job['user_id'] = D_results['UID']

    # Unsure what to call this.
    D_job['cc_account_username'] = D_results['User']

    D_job['job_state'] = D_results['State']
    D_job['partition'] = D_results['Partition']

    # This is a bit strange because sometimes we have a 'JobIdRaw' that doesn't match.
    # You might think that JobID should be an integer, but it gets
    # values like '3114459_1.batch' so it's not an integer.
    D_job['job_id'] = D_results['JobID']

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

    #### Submit ####
    D_job['submit_time'] = int(localtime_to_unix_timestamp(D_results['Submit']))
    #### Start ####
    if D_results['Start'] is None or D_results['Start'] == "Unknown":
        D_job['start_time'] = None
    else:
        D_job['start_time'] = int(localtime_to_unix_timestamp(D_results['Start']))
    #### End ####
    if D_results['End'] is None or D_results['End'] == "Unknown":
        D_job['end_time'] = None
    else:
        D_job['end_time'] = int(localtime_to_unix_timestamp(D_results['End']))
    #### Eligible ####
    D_job['eligible_time'] = int(localtime_to_unix_timestamp(D_results['Eligible']))
    ####

    # No idea what this does, but the mapping seems natural.
    D_job['assoc_id'] = int(D_results['AssocID'])

    """
        "time_limit": 900,
        "time_limit_str": "15:00:00",
        "Timelimit": "23:59:00",
        "TimelimitRaw": "1439",
    """
    D_job['time_limit'] = int(D_results['TimelimitRaw']) if D_results['TimelimitRaw'] else 0
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




#### functions for `sinfo` ####

"""
AVAIL|ACTIVE_FEATURES|CPUS|TMP_DISK|FREE_MEM|AVAIL_FEATURES|GROUPS|OVERSUBSCRIBE|TIMELIMIT|MEMORY|HOSTNAMES|NODE_ADDR|PRIO_TIER|ROOT|JOB_SIZE|STATE|USER|VERSION|WEIGHT|S:C:T|NODES(A/I) |MAX_CPUS_PER_NODE |CPUS(A/I/O/T) |NODES |REASON |NODES(A/I/O/T) |GRES |TIMESTAMP |PRIO_JOB_FACTOR |DEFAULTTIME |PREEMPT_MODE |NODELIST |CPU_LOAD |PARTITION |PARTITION |ALLOCNODES |STATE |USER |CLUSTER |SOCKETS |CORES |THREADS 
up|broadwell|32|864097|40390|broadwell|all|NO|3-00:00:00|128000|cdr2|cdr2|10|no|1-infinite|alloc|Unknown|20.11.7|114|2:16:1|1/0 |UNLIMITED |32/0/0/32 |1 |none |1/0/0/1 |(null) |Unknown |5 |1:00:00 |OFF |cdr2 |30.11 |cpubase_bycore_b4 |cpubase_bycore_b4 |cedar[1,5],lcg-ce[1,2,3],cedar1.cedar.computecanada.ca,cedar5.cedar.computecanada.ca,gateway,gateway.int.cedar.computecanada.ca,jupyterhub,jupyterhub.cedar.computecanada.ca,jupyterhub.int.cedar.computecanada.ca,lcg-ce1.sfu.computecanada.ca,lcg-ce2.sfu.computecanada.ca,lcg-ce3.sfu.computecanada.ca,cdr[1-2999] |allocated |Unknown |N/A |2 |16 |1 

    {
        "ACTIVE_FEATURES": "p100",
        "ALLOCNODES ": "cedar[1,5],lcg-ce[1,2,3],cedar1.cedar.computecanada.ca,cedar5.cedar.computecanada.ca,gateway,gateway.int.cedar.computecanada.ca,jupyterhub,jupyterhub.cedar.computecanada.ca,jupyterhub.int.cedar.computecanada.ca,lcg-ce1.sfu.computecanada.ca,lcg-ce2.sfu.computecanada.ca,lcg-ce3.sfu.computecanada.ca,cdr[1-2999] ",
        "AVAIL": "up",
        "AVAIL_FEATURES": "p100",
        "CLUSTER ": "N/A ",
        "CORES ": "12 ",
        "CPUS": "24",
        "CPUS(A/I/O/T) ": "20/4/0/24 ",
        "CPU_LOAD ": "5.74 ",
        "DEFAULTTIME ": "1:00:00 ",
        "FREE_MEM": "81843",
        "GRES ": "gpu:p100:4 ",
        "GROUPS": "all",
        "HOSTNAMES": "cdr33",
        "JOB_SIZE": "1-infinite",
        "MAX_CPUS_PER_NODE ": "UNLIMITED ",
        "MEMORY": "128000",
        "NODELIST ": "cdr33 ",
        "NODES ": "1 ",
        "NODES(A/I) ": "1/0 ",
        "NODES(A/I/O/T) ": "1/0/0/1 ",
        "NODE_ADDR": "cdr33",
        "OVERSUBSCRIBE": "NO",
        "PARTITION ": "gpubase_bygpu_b1 ",
        "PREEMPT_MODE ": "OFF ",
        "PRIO_JOB_FACTOR ": "11 ",
        "PRIO_TIER": "10",
        "REASON ": "none ",
        "ROOT": "no",
        "S:C:T": "2:12:1",
        "SOCKETS ": "2 ",
        "STATE": "mix",
        "STATE ": "mixed ",
        "THREADS \n": "1 ",
        "TIMELIMIT": "3:00:00",
        "TIMESTAMP ": "Unknown ",
        "TMP_DISK": "711548",
        "USER": "Unknown",
        "USER ": "Unknown ",
        "VERSION": "20.11.7",
        "WEIGHT": "614"
    },

"""


def load_sinfo_stdout(L_lines):
    """
    Whereas "sacct --parsable" puts a pipe at the end of the line for no good reason,
    "sinfo" does not do that. We parse its output in a more straightforward way.
    """

    LD = []
    # Note that we have two instances of "STATE" and "STATE "
    # and we're interested only in the one corresponding to "STATE "
    # because it's the longer version.
    # We're saved by the fact that
    #     dict([ (1, 2), (1,3) ]) is {1:3} and not {1:2},
    # and "STATE " comes later in the enumeration by the sinfo command.
    header = [e.replace("\n", "").replace(" ", "") for e in L_lines[0].split("|")]
    for line in L_lines[1:]:
        line = line.replace("\n", "")
        if not line:
            continue
        tokens = line.split("|")

        D = dict(zip(header, tokens))
        LD.append(D)

    return LD


def analyze_sinfo_json(LD_nodes_original, cluster_name="cedar"):
    """
    Basically, we're going to collapse everything as a dict based on 'HOSTNAMES'.
    Entries in `LD_nodes_original` contain a duplicate for each 'PARTITION'.

    We are going to create new entries

        D_node_original['HOSTNAMES']:
            {
                'cluster_name': 'cedar',
                'host': D_node_original['HOSTNAMES'],
                'partitions': < here we aggregate the values of D_node_original['PARTITION']>,
                ...
                'gres': D_node_original['GRES'],
                'free_mem': D_node_original['FREE_MEM'],
                ...
            }

    and stick them into the same dict in order to match
    the structure given to us by pyslurm.
    """

    psl_nodes = {}

    for D_node in LD_nodes_original:

        name = D_node['HOSTNAMES']
        assert re.match(r"^[a-zA-Z\d\-]+$", name)
        if name in psl_nodes:
            # If we already have that entry, just add the partition name and we're done.
            psl_nodes[name]['partitions'].append( D_node['PARTITION'] )
        else:
            # Otherwise we're going to translate values.
            # Note difficulties such as
            #         "STATE": "mix",
            #         "STATE ": "mixed ",
            # where we'll decide to grab "STATE " with a space
            # because it appears to be the long form.

            # "CPUS(A/I/O/T) ": "20/4/0/24 ",
            alloc_cpus, idle_cpus, other_cpus, total_cpus = [int(n) for n in D_node['CPUS(A/I/O/T)'].split('/')]
            # not using "idle_cpus" nor "total_cpus" (the latter being inferred by the field "cpus")

            psl_nodes[name] = {
                'name': name,
                'cluster_name': cluster_name,
                'partitions': [ D_node['PARTITION'] ], # will be append to, later
                'cores': int(D_node["CORES"]),
                'cpu_load': float(D_node["CPU_LOAD"]) if "N/A" not in D_node["CPU_LOAD"] else 0,
                'alloc_cpus': alloc_cpus,
                'err_cpus': other_cpus,  # "other" gets interpreted as "error"
                'cpus': int(D_node["CPUS"]),
                'gres': [D_node["GRES"].replace(" ", "")] if "null" not in D_node["GRES"] else [],
                'gres_used': [],
                # would be nice to have some kind of 'gres_used' but it's not there
                'node_addr': D_node['NODE_ADDR'],
                'state': D_node['STATE'].replace(" ", ""),
                'reason': D_node['REASON'],
                'tmp_disk': D_node['TMP_DISK'],
                'version': D_node['VERSION'],
                'weight': int(D_node['WEIGHT']),
                'reservation': "None"  # because it's missing and "None" is the symbol we use for that
            }
    return psl_nodes






def main():
    # valid_sacct_fields = get_valid_sacct_fields()
    # print(valid_sacct_fields)

    desired_sacct_fields = get_desired_sacct_fields()

    accounts = ",".join(get_accounts())
    format = ",".join(desired_sacct_fields) #[e.lower() for e in valid_sacct_fields])
    delimiter = "|"

    cmd = f"sacct --allusers --accounts {accounts} --format {format} --delimiter '{delimiter}' --parsable"
    # print(cmd)
    L_lines = [e for e in subprocess.check_output(cmd, shell=True, encoding='utf8').split("\n") if len(e)>0]
 
    LD_jobs = []
    # skip the header in L_lines[0]
    for line in L_lines[1:]:
        LD_jobs.append( analyze_stdout_line(desired_sacct_fields, line, delimiter) )

    # with open("sinfo_LD_jobs.json", "w") as f:
    #     json.dump(LD_jobs, f)
    # pprint(json.dumps(LD_jobs))

    # This is what will be returned. We format it as a dict with keys
    # given by job_id in order to match the format from pyslurm.
    LD_jobs_as_pyslurm_format = [translate_sacct_format_into_pyslurm_format(D_job) for D_job in LD_jobs]
    psl_jobs = dict((D_job['job_id'], D_job) for D_job in LD_jobs_as_pyslurm_format)




    cmd = "sinfo --Format All --Node"
    L_lines = [e for e in subprocess.check_output(cmd, shell=True, encoding='utf8').split("\n") if len(e)>0]

    # We hardcoded here that this would run on `cedar` because it's the only cluster
    # where we need to run this like that.
    psl_nodes = analyze_sinfo_json(load_sinfo_stdout(L_lines), cluster_name="cedar")


    results = { 'node': psl_nodes,
                'reservation': {},
                'job': psl_jobs}

    with open("/home/alaingui/last_sacct_sinfo_data.json", "w") as f:
        json.dump(results, f)

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
    rsync -av ${HOME}/Documents/code/slurm_monitoring_and_reporting/slurm_monitoring_and_reporting/manual_flimsy_sinfo_scraper.py cedar:bin

    ssh cedar 'sinfo --Format All --Node' > cedar_sinfo.txt

    ssh cedar 'module load python/3.6.10; python3 ${HOME}/bin/manual_flimsy_sinfo_scraper.py' > cedar_three_components.json
"""