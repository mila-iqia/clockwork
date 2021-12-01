from slurm_state.anonymize_scontrol_report import process_line


def test_process_line_job():

    D_user = {
        "username": "some_user",
        "uid": 10000,
        "account": "mila",
        "cluster_name": "mila",
    }

    L_lines = """
JobId=01234567 JobName=secret_01234567
   UserId=secret(01234567) GroupId=secret(01234567) MCS_label=N/A
   Priority=0 Nice=0 Account=secret-rrg QOS=normal
   JobState=PENDING Reason=JobHeldUser Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=00:00:00 TimeLimit=03:00:00 TimeMin=N/A
   SubmitTime=2020-02-04T03:22:55 EligibleTime=2020-02-04T03:22:57
   AccrueTime=Unknown
   StartTime=Unknown EndTime=Unknown Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2020-02-04T03:23:28
   Partition=secret,cpubackfill AllocNode:Sid=secret:225182
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=(null)
   NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=1,mem=6000M,node=1,billing=1
   Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
   MinCPUsNode=1 MinMemoryCPU=6000M MinTmpDiskNode=0
   Features=(null) DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=secret
   WorkDir=secret
   StdErr=/a/secret.err
   StdIn=/dev/secret
   StdOut=/a/secret.out
   Power=
    """.split(
        "\n"
    )

    for line in L_lines:
        line_done = process_line(line, D_user)
        assert "secret" not in line_done
        assert "01234567" not in line_done


def test_process_line_node():

    D_user = {
        "cluster_name": "mila",
    }

    L_lines = """
NodeName=secret4104 Arch=x86_64 CoresPerSocket=2
   CPUAlloc=6 CPUTot=40 CPULoad=0.01
   AvailableFeatures=skylake,v100,nvlink
   ActiveFeatures=skylake,v100,nvlink
   Gres=gpu:v100:4
   NodeAddr=secret4104 NodeHostName=secret4104  Port=0 Version=19.05.8
   OS=Linux 17.10.secret.x86_64
   RealMemory=191000 AllocMem=32000 FreeMem=115949 Sockets=2 Boards=1
   State=MIXED ThreadsPerCore=1 TmpDisk=1412000 Weight=4 Owner=N/A MCS_label=N/A
   Partitions=secret
   BootTime=2021-11-11T15:08:38 SlurmdStartTime=2021-11-11T15:13:38
   CfgTRES=cpu=40,mem=191000M,billing=4,gres/gpu=4
   AllocTRES=cpu=6,mem=32000M,gres/gpu=1
   CapWatts=n/a
   CurrentWatts=0 AveWatts=0
   ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s
    """.split(
        "\n"
    )

    for line in L_lines:
        assert "secret" not in process_line(line, D_user)
