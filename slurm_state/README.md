# Slurm Scan

## intention

This is a rewrite of "slurm_monitor", which was itself based on the "sinfo.py" script.
Many factors have lead me to think that parsing the output of "sacct" and "sinfo" commands
is unfortunately the best that we can currently build on, given the unrealiability of PySlurm
when it comes to supporting the latest version of Slurm.

Moreover, I no longer support the idea of having the data scraping
and processing be done in the same script as the serving of
Prometheus endpoints (as well as populating of ElasticSearch).
There is a way to do all that, but without creating a monolithic script.

Compute Canada have also pointed me towards their own automated scripts
that periodically (every 10 minutes) call sacct/sinfo and write the output
to the shared file system. See note in section below.



## `mila-automation` accounts

When running in production, we will use a special user account that does
not belong to a particular Mila member. Compute Canada has a special account
made for that purpose.

|cluster | automation account | who has access at the moment |
|--------|--------------------|------------------------------|
| mila   | ???                | guillaume alain |
| cedar  | mila-automation    | guillaume alain |
| beluga | mila-automation    | guillaume alain |
| graham | mila-automation    | guillaume alain |

## dev notes

- Voir comment je gère mongoclient dans le web, et faire ça dans slurm_scan.

## TODO:

- Remove "alaingui" from the "remote_clusters_info.json".

- One of the important things for clockwork_web_test is the fake_data.json.
However, when we update "slurm_state" according to a certain structure for
the slurm data, as returned by sacct/sinfo instead of pyslurm, then we
should update fake_data.json to reflect that structure.
This isn't hard, but it requires diligence.

- Share the access to "mila-automation" with Arnaud.
This should also be documented better in terms of which account should be
used for tools on what cluster.



# Compute Canada giving us stdout

## cached results

Tyler Collin discussed with us the possible ways to
make our requests as light as possible on their servers.
One thing that came up was the fact that they collect the
values returned by sacct/sinfo every 10 minutes and write them
on the shared file system.

We were encouraged to copy the files without any processing,
and do all the processing on our side (to avoid imposing a load
on the login nodes).

| cluster | location for scripts and outputs |
|--|--|
| cedar | /project/cc/slurm |
| beluga | /lustre04/cc/slurm |
| graham | /opt/software/slurm/clusterstats_cache |

## scripts run

The scripts run periodically (by the people at Compute Canada) are the following.
One of the reasons to care about this is that, if we're going to be writing
a parser for their files, then we have an incentive to generate files with
the same formatting on the Mila cluster.

```
#!/bin/bash

TARGET_DIR="/project/cc/slurm"
SHOW_JOB_DEST="scontrol_show_job"
SHOW_NODE_DEST="scontrol_show_node"
SSHARE_DEST="sshare_plan"

/opt/software/slurm/bin/scontrol show job  > "${TARGET_DIR}/${SHOW_JOB_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SHOW_JOB_DEST}.tmp" "${TARGET_DIR}/${SHOW_JOB_DEST}"
/opt/software/slurm/bin/scontrol show node > "${TARGET_DIR}/${SHOW_NODE_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SHOW_NODE_DEST}.tmp" "${TARGET_DIR}/${SHOW_NODE_DEST}"
/opt/software/slurm/bin/sshare -Plan       > "${TARGET_DIR}/${SSHARE_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SSHARE_DEST}.tmp" "${TARGET_DIR}/${SSHARE_DEST}"
```

## stdout format

We show here examples of some lines from the files collected by Compute Canada.
Instead of serializing all the fields on a single line, individual entries
are broken into many lines, with empty lines between each entries.

### head -n 36 scontrol_show_node

```
NodeName=cdr2 Arch=x86_64 CoresPerSocket=16 
   CPUAlloc=32 CPUTot=32 CPULoad=56.14
   AvailableFeatures=broadwell
   ActiveFeatures=broadwell
   Gres=(null)
   NodeAddr=cdr2 NodeHostName=cdr2 Version=20.11.7
   OS=Linux 3.10.0-1160.36.2.el7.x86_64 #1 SMP Wed Jul 21 11:57:15 UTC 2021 
   RealMemory=128000 AllocMem=117188 FreeMem=44208 Sockets=2 Boards=1
   State=ALLOCATED ThreadsPerCore=1 TmpDisk=864097 Weight=114 Owner=N/A MCS_label=N/A
   Partitions=cpubase_bycore_b4,cpubase_bycore_b3,cpubase_bycore_b2,cpubase_bycore_b1,cpubase_bynode_b4,cpubase_bynode_b3,cpubase_bynode_b2,cpubase_bynode_b1,cpubackfill,c12hbackfill,cpupreempt 
   BootTime=2021-08-30T10:39:25 SlurmdStartTime=2021-08-30T10:46:39
   CfgTRES=cpu=32,mem=125G,billing=32
   AllocTRES=cpu=32,mem=117188M
   CapWatts=n/a
   CurrentWatts=0 AveWatts=0
   ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s
   Comment=(null)

NodeName=cdr3 Arch=x86_64 CoresPerSocket=16 
   CPUAlloc=32 CPUTot=32 CPULoad=26.92
   AvailableFeatures=broadwell
   ActiveFeatures=broadwell
   Gres=(null)
   NodeAddr=cdr3 NodeHostName=cdr3 Version=20.11.7
   OS=Linux 3.10.0-1160.36.2.el7.x86_64 #1 SMP Wed Jul 21 11:57:15 UTC 2021 
   RealMemory=128000 AllocMem=110451 FreeMem=43820 Sockets=2 Boards=1
   State=ALLOCATED ThreadsPerCore=1 TmpDisk=864097 Weight=114 Owner=N/A MCS_label=N/A
   Partitions=cpubase_bycore_b4,cpubase_bycore_b3,cpubase_bycore_b2,cpubase_bycore_b1,cpubase_bynode_b4,cpubase_bynode_b3,cpubase_bynode_b2,cpubase_bynode_b1,cpubackfill,c12hbackfill,cpupreempt 
   BootTime=2021-07-29T04:21:00 SlurmdStartTime=2021-07-29T04:28:49
   CfgTRES=cpu=32,mem=125G,billing=32
   AllocTRES=cpu=32,mem=110451M
   CapWatts=n/a
   CurrentWatts=0 AveWatts=0
   ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s
   Comment=(null)
```

### head -n 55 scontrol_show_job

```
JobId=57663829 JobName=slurm_run.sh
   UserId=hahn(3000566) GroupId=hahn(3000566) MCS_label=N/A
   Priority=0 Nice=0 Account=def-hahn_cpu QOS=normal
   JobState=PENDING Reason=JobHeldUser Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=00:00:00 TimeLimit=01:00:00 TimeMin=N/A
   SubmitTime=2020-12-18T11:37:51 EligibleTime=Unknown
   AccrueTime=Unknown
   StartTime=Unknown EndTime=Unknown Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2020-12-18T11:37:51
   Partition=cpubase_bycore_b1,cpubackfill,c12hbackfill AllocNode:Sid=cedar5.cedar.computecanada.ca:24591
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=(null)
   NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=1,mem=256M,node=1,billing=1
   Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
   MinCPUsNode=1 MinMemoryCPU=256M MinTmpDiskNode=0
   Features=[broadwell|skylake|cascade] DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/home/hahn/slurm_run.sh hostname
   WorkDir=/project/6000288
   StdErr=/project/6000288/slurm-57663829.out
   StdIn=/dev/null
   StdOut=/project/6000288/slurm-57663829.out
   Power=
   NtasksPerTRES:0

JobId=2574367 JobName=ph11_mm_ext3_dpl
   UserId=rossta(3048724) GroupId=rossta(3048724) MCS_label=N/A
   Priority=1913480 Nice=0 Account=def-browna_cpu QOS=normal
   JobState=PENDING Reason=Priority Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=00:00:00 TimeLimit=2-12:00:00 TimeMin=N/A
   SubmitTime=2021-05-16T09:31:04 EligibleTime=2021-05-16T09:31:04
   AccrueTime=2021-05-16T09:31:04
   StartTime=Unknown EndTime=Unknown Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2021-09-23T06:58:27
   Partition=cpularge_bycore_b4 AllocNode:Sid=cedar1.cedar.computecanada.ca:26488
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=(null)
   NumNodes=14-14 NumCPUs=224 NumTasks=224 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=224,mem=3360000M,node=14,billing=820
   Socks/Node=* NtasksPerN:B:S:C=16:0:*:* CoreSpec=*
   MinCPUsNode=16 MinMemoryCPU=15000M MinTmpDiskNode=0
   Features=[broadwell|skylake|cascade] DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/project/6001042/rossta/mfruits/mpa/sub_dpl_pem_mcher_p11_mm_ext3.sh
   WorkDir=/project/6001042/rossta/mfruits/mpa
   StdErr=/project/6001042/rossta/mfruits/mpa/slurm-2574367.out
   StdIn=/dev/null
   StdOut=/project/6001042/rossta/mfruits/mpa/slurm-2574367.out
   Power=
   NtasksPerTRES:0
```

### head sshare_plan

```
[alaingui@cedar1 slurm]$ head sshare_plan 
def-arasmus_cpu|blm708|1|0.000000|0||0.000000|0.000000|0.000000||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
def-arasmus_gpu|blm708|1|0.000000|0||0.000000|0.000000|0.000000||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
def-ranil-ab_gpu|cooko|1|0.166667|0|0.000000|0.000000|0.695677|inf||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
def-ranil-ab_cpu|cooko|1|0.166667|0|0.000000|0.000000|0.695828|inf||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
root|||0.000000|91640356437||1.000000||||cpu=376158997,mem=1407754764774,energy=0,node=71636833,billing=427551679,fs/disk=0,vmem=0,pages=0,gres/gpu=3468175
root|root|0|0.000000|0|0.000000|0.000000|0.186134|0.000000||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
 aiuo-wa_gpu||0|0.000000|0|0.000000|0.000000||0.000000||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
  aiuo-wa_gpu|dswailum|1|0.047619|0|0.000000|0.000000|0.186134|inf||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
  aiuo-wa_gpu|gpsingh|1|0.047619|0|0.000000|0.000000|0.186134|inf||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
  aiuo-wa_gpu|guest107|1|0.047619|0|0.000000|0.000000|0.186134|inf||cpu=0,mem=0,energy=0,node=0,billing=0,fs/disk=0,vmem=0,pages=0,gres/gpu=0
```