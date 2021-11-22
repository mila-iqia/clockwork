import re
import datetime

FIELD = re.compile(r"([a-zA-z/:]+)=(.*?)(?: ([a-zA-Z/:]+=.*)|$)")


def gen_dicts(f):
    """Yields dicts from blocks in the 'scontrol show' output format."""
    curd = dict()
    for line in f:
        line = line.strip()
        if line == "":
            if curd:
                yield curd
            curd = dict()
            continue
        while line:
            m = FIELD.match(line)
            if m is None:
                # Of course slrum needs to throw in a field with a different
                # format at the end, because why not.
                if line == "NtasksPerTRES:0":
                    line = ""
                    continue
                raise ValueError("Unexpected non-matching expression: " + line)
            curd[m.group(1)] = m.group(2)
            line = m.group(3)
    if curd:
        yield curd


def ignore(f, ctx, res):
    pass


def rename(fn, name):
    def renamer(f, ctx, res):
        val = fn(f, ctx)
        res[name] = val

    return renamer


def dynrename(fn, ctx_key):
    def dynrenamer(f, ctx, res):
        val = fn(f, ctx)
        res[ctx[ctx_key]] = val
        # res[getattr(ctx, ctx_key)] = val

    return dynrenamer


def id(f, ctx):
    """Return the field as-is."""
    return f


def account(f, ctx):
    return f.split("(")[0]


def maybe_null_string_to_none_object(f, ctx):
    """
    Converts "(null)" into `None` if applicable.
    Otherwise, leaves the field unchanged.
    """
    if f == "(null)":
        return None
    else:
        return f


TIMELIMIT = re.compile(r"(?:(?:(?:(\d+)-)?(\d\d):)?(\d\d):)?(\d\d)", re.ASCII)


def timelimit(f, ctx):
    m = TIMELIMIT.fullmatch(f)
    if m is None:
        raise ValueError(f"Unknown time limit format: {f}")
    days, hours, minutes, seconds = map(
        lambda t: 0 if t is None else int(t), m.groups()
    )
    return seconds + 60 * minutes + 3600 * hours + 86400 * days


def timestamp(f, ctx):
    # We add the timezone information for the timestamp
    if f == "Unknown":
        return f
    date_naive = datetime.datetime.strptime(f, "%Y-%m-%dT%H:%M:%S")
    date_aware = date_naive.replace(tzinfo=ctx["timezone"])
    return date_aware.isoformat()


# This map should contain all the fields that come from parsing a job entry
# Each field should be mapped to a handler that will process the string data
# and set the result in the output dictionary.  You can ignore fields, by
# assigning them to 'ignore'
JOB_FIELD_MAP = {
    "JobId": rename(id, "job_id"),
    # maybe we shouldn't ignore
    "ArrayJobId": ignore,
    "ArrayTaskId": ignore,
    "ArrayTaskThrottle": ignore,
    "JobName": rename(id, "name"),
    "UserId": dynrename(account, "local_username_referenced_by_parent_as"),
    "GroupId": ignore,
    "MCS_label": ignore,
    "Priority": ignore,
    "Nice": ignore,
    "Account": rename(id, "account"),
    "QOS": ignore,
    "JobState": rename(id, "job_state"),
    "Reason": ignore,
    "Dependency": ignore,
    "Requeue": ignore,
    "Restarts": ignore,
    "BatchFlag": ignore,
    "Reboot": ignore,
    "ExitCode": rename(id, "exit_code"),
    "RunTime": ignore,
    "TimeLimit": rename(timelimit, "time_limit"),
    "TimeMin": ignore,
    "SubmitTime": rename(timestamp, "submit_time"),
    "EligibleTime": ignore,
    "AccrueTime": ignore,
    "StartTime": rename(timestamp, "start_time"),
    "EndTime": rename(timestamp, "end_time"),
    "Deadline": ignore,
    "PreemptEligibleTime": ignore,
    "PreemptTime": ignore,
    "SuspendTime": ignore,
    "SecsPreSuspend": ignore,
    "LastSchedEval": ignore,
    "Partition": rename(id, "partition"),
    "AllocNode:Sid": ignore,
    # We can do these one maybe
    "ReqNodeList": ignore,
    "ExcNodeList": ignore,
    # I don't see jobs with more than one node for now
    "NodeList": rename(maybe_null_string_to_none_object, "nodes"),
    "SchedNodeList": ignore,
    "BatchHost": ignore,
    "NumNodes": ignore,
    "NumCPUs": ignore,
    "NumTasks": ignore,
    "CPUs/Task": ignore,
    "ReqB:S:C:T": ignore,
    # maybe not?
    "TRES": ignore,
    "Socks/Node": ignore,
    "NtasksPerN:B:S:C": ignore,
    "CoreSpec": ignore,
    "MinCPUsNode": ignore,
    "MinMemoryCPU": ignore,
    "MinMemoryNode": ignore,
    "MinTmpDiskNode": ignore,
    "Features": ignore,
    "DelayBoot": ignore,
    "Reservation": rename(id, "resv_name"),
    "OverSubscribe": ignore,
    "Contiguous": ignore,
    "Licenses": ignore,
    "Network": ignore,
    # this is probably not right
    "Command": rename(maybe_null_string_to_none_object, "command"),
    "WorkDir": rename(id, "work_dir"),
    "StdErr": rename(id, "stderr"),
    "StdIn": rename(id, "stdin"),
    "StdOut": rename(id, "stdout"),
    "Power": ignore,
    "CpusPerTres": ignore,
    # maybe not?
    "TresPerNode": ignore,
    "MailUser": ignore,
    "MailType": ignore,
    # seems like "Comment" pops up on other clusters
    "Comment": rename(maybe_null_string_to_none_object, "comment"),
    "TresPerJob": ignore,
    "Switches": ignore,
    "TresPerTask": ignore,
    "MemPerTres": ignore,
    "CPU_max_freq": ignore,
}


def job_parser(f, ctx):
    """Parse a file of job entries.

    This is an iterator that will yield a dict for each job entry with
    the fields mapped according to JOB_FIELD_MAP.

    Unknown fields will raise an error.
    """
    for d in gen_dicts(f):
        res = dict()
        command_hack = False
        v_acc = None
        saved_m = None
        for k, v in d.items():
            m = JOB_FIELD_MAP.get(k, None)
            if m is None:
                if command_hack:
                    # If we encounter an invalid field while doing the
                    # command hack, then it must have been part of the command.
                    v_acc = v_acc + f" {k}={v}"
                    continue
                raise ValueError(f"Unknown field in job output: {k}")
            if k == "Command" and not command_hack:
                # The Command field can have things that look like fields in
                # it. We attempt to fix this here by appending those to the
                # command value, but this can be defeated if a program takes
                # a "field" that is shared with slurm as an input.
                command_hack = True
                v_acc = v
                saved_m = m
                continue
            if command_hack:
                # If we are doing the command hack, but we encouter
                # a valid field, then we terminate it.
                saved_m(v_acc, ctx, res)
                command_hack = False
                v_acc = None
                saved_m = None
            m(v, ctx, res)
        else:
            # If we end the fields for the dict while doing the command hack,
            # add the gathered command to the result.
            if command_hack:
                saved_m(v_acc, ctx, res)
                command_hack = False
                v_acc = None
                saved_m = None
        yield res


NODE_FIELD_MAP = {
    "NodeName": rename(id, "name"),
    "Arch": rename(id, "arch"),
    "CoresPerSocket": ignore,
    "CPUAlloc": ignore,
    "CPUTot": ignore,
    "CPULoad": ignore,
    "AvailableFeatures": rename(id, "features"),
    "ActiveFeatures": ignore,
    "Gres": rename(maybe_null_string_to_none_object, "gres"),
    "NodeAddr": rename(id, "addr"),
    "NodeHostName": ignore,
    "Version": ignore,
    "OS": ignore,
    "RealMemory": rename(id, "memory"),
    "AllocMem": ignore,
    "FreeMem": ignore,
    "Sockets": ignore,
    "Boards": ignore,
    "State": rename(id, "state"),
    "ThreadsPerCore": ignore,
    "TmpDisk": ignore,
    "Weight": ignore,
    "Owner": ignore,
    "MCS_label": ignore,
    "Partitions": ignore,
    "BootTime": ignore,
    "SlurmdStartTime": ignore,
    # Probably better to parse these
    "CfgTRES": rename(id, "cfg_tres"),
    "AllocTRES": rename(id, "alloc_tres"),
    "CapWatts": ignore,
    "CurrentWatts": ignore,
    "AveWatts": ignore,
    "ExtSensorsJoules": ignore,
    "ExtSensorsWatts": ignore,
    "ExtSensorsTemp": ignore,
    "Reason": rename(id, "reason"),
    "Comment": rename(maybe_null_string_to_none_object, "comment"),
    # added by gyom (to be discussed),
    "NextState": ignore,
    "Port": ignore,
}


def node_parser(f, ctx):
    """Parse a file of node entries.

    This is an iterator that will yield a dict for each node entry with
    the fields mapped according to NODE_FIELD_MAP.

    Unknown fields will raise an error.
    """
    for d in gen_dicts(f):
        res = dict()
        for k, v in d.items():
            m = NODE_FIELD_MAP.get(k, None)
            if m is None:
                raise ValueError(f"Unknown field in node output: {k}")
            m(v, ctx, res)
        yield res
