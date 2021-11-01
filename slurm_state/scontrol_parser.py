import re
import datetime

FIELD = re.compile(r"([a-zA-z/:]+)=(.*?)(?: ([a-zA-Z]+=.*)|$)")


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

    # copy over the properties of 'fn' to renamer
    return renamer


def id(f, ctx):
    """Return the field as-is."""
    return f


def account(f, ctx):
    return f.split("(")[0]


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
    date_aware = date_naive.replace(tzinfo=ctx.timezone)
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
    "UserId": rename(account, "cc_account_username"),
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
    "NodeList": rename(id, "nodes"),
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
    "Command": rename(id, "command"),
    "WorkDir": rename(id, "work_dir"),
    "StdErr": ignore,
    "StdIn": ignore,
    "StdOut": ignore,
    "Power": ignore,
    "CpusPerTres": ignore,
    # maybe not?
    "TresPerNode": ignore,
    "MailUser": ignore,
    "MailType": ignore,
}


def job_parser(f, ctx):
    """."""
    for d in gen_dicts(f):
        res = dict()
        for k, v in d.items():
            m = JOB_FIELD_MAP.get(k, None)
            if m is None:
                raise ValueError(f"Unknown field in job output: {k}")
            m(v, ctx, res)
        yield res
