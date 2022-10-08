import pytest
from io import StringIO
from slurm_state.scontrol_parser import *
import zoneinfo
from datetime import datetime


def test_gen_dicts_2fields():
    f = StringIO("Name=test data=12")
    res = list(gen_dicts(f))
    assert res == [dict(Name="test", data="12")]


def test_gen_dicts_spaces():
    f = StringIO("LongField=some text with spaces")
    res = list(gen_dicts(f))
    assert res == [dict(LongField="some text with spaces")]


def test_gen_dicts_newline():
    f = StringIO(
        """Name=test
   data=12
"""
    )
    res = list(gen_dicts(f))
    assert res == [dict(Name="test", data="12")]


def test_gen_dicts_equals():
    f = StringIO("data=a=1,b=2")
    res = list(gen_dicts(f))
    assert res == [dict(data="a=1,b=2")]


def test_gen_dicts_colon():
    f = StringIO("partition=long field:val=result:33")
    res = list(gen_dicts(f))
    assert res == [{"partition": "long", "field:val": "result:33"}]


def test_gen_dicts_split():
    f = StringIO(
        """Name=1
   data=12

Name=2
  data=11
"""
    )
    res = list(gen_dicts(f))
    assert res == [dict(Name="1", data="12"), dict(Name="2", data="11")]


def test_gen_dicts_trailing_lines():
    f = StringIO(
        """Name=1 data=12



"""
    )
    res = list(gen_dicts(f))
    assert res == [dict(Name="1", data="12")]


def test_gen_dicts_slurm_ending():
    f = StringIO(
        """Name=1 data=12
   NtasksPerTRES:0

"""
    )
    res = list(gen_dicts(f))
    assert res == [dict(Name="1", data="12")]


def test_gen_dict_invalid_field():
    f = StringIO(
        """Name=1
   potato

"""
    )
    g = gen_dicts(f)
    with pytest.raises(ValueError):
        print(list(g))


def test_ignore():
    d = {}
    ignore("1", None, d)
    assert len(d) == 0


def test_rename():
    fn = rename(id, "name")
    d = {}
    fn("1", None, d)
    assert d == {"name": "1"}


def test_dynrename():
    fn = dynrename(id, "user_field")

    ctx = {"user_field": "test_user"}

    d = {}
    fn("name", ctx, d)
    assert d == {"test_user": "name"}


def test_id():
    assert id("1", None) == "1"


def test_id_int():
    assert id_int("1", None) == 1


def test_user_id_splitting():

    d = {}
    user_id_splitting(
        "luigi(633819)",
        None,
        d,
    )
    assert d["username"] == "luigi"
    assert d["uid"] == 633819


def test_maybe_null_string():
    assert maybe_null_string_to_none_object("(null)", None) is None
    assert maybe_null_string_to_none_object("(null", None) == "(null"
    assert maybe_null_string_to_none_object("name", None) == "name"


def test_timelimit():
    assert timelimit("7-00:00:00", None) == 604800
    assert timelimit("12:00:00", None) == 43200
    assert timelimit("10:00", None) == 600
    assert timelimit("22", None) == 22
    with pytest.raises(ValueError):
        timelimit("abcd", None)


def test_timestamp():

    ctx = {}
    ctx["timezone"] = zoneinfo.ZoneInfo("America/Montreal")
    assert (
        timestamp("2021-12-24T12:34:56", ctx)
        == datetime.fromisoformat("2021-12-24T12:34:56-05:00").timestamp()
    )
    assert (
        timestamp("2021-06-24T12:34:56", ctx)
        == datetime.fromisoformat("2021-06-24T12:34:56-04:00").timestamp()
    )

    ctx["timezone"] = zoneinfo.ZoneInfo("America/Vancouver")
    assert (
        timestamp("2021-12-24T12:34:56", ctx)
        == datetime.fromisoformat("2021-12-24T12:34:56-08:00").timestamp()
    )
    assert (
        timestamp("2021-06-24T12:34:56", ctx)
        == datetime.fromisoformat("2021-06-24T12:34:56-07:00").timestamp()
    )

    assert timestamp("Unknown", ctx) == None


def test_job_parser():
    f = StringIO(
        """JobId=123 JobName=sh

JobId=124 JobName=sh

"""
    )

    assert list(job_parser(f, None)) == [
        {"job_id": "123", "name": "sh"},
        {"job_id": "124", "name": "sh"},
    ]


def test_job_parser_error():
    f = StringIO(
        """potato=123 JobName=sh

"""
    )
    p = job_parser(f, None)
    with pytest.raises(ValueError):
        list(p)


def test_job_parser_command_hack():
    f = StringIO(
        """JobId=123 JobName=bash
  Command=script arg=1;val=2
  Account=user
"""
    )
    assert list(job_parser(f, None)) == [
        {
            "job_id": "123",
            "name": "bash",
            "command": "script arg=1;val=2",
            "account": "user",
        },
    ]


def test_job_parser_command_hack_end():
    f = StringIO(
        """JobId=123 JobName=bash
  Command=script arg=1;val=2
"""
    )
    assert list(job_parser(f, None)) == [
        {"job_id": "123", "name": "bash", "command": "script arg=1;val=2"},
    ]


def test_node_parser():
    f = StringIO(
        """NodeName=abc1 Arch=x86_64 Gres=gpu:rtx8000:8(S:0-1)

NodeName=abc2 Arch=power9

"""
    )
    assert list(node_parser(f, None)) == [
        {
            "name": "abc1",
            "arch": "x86_64",
            "gres": "gpu:rtx8000:8(S:0-1)",
        },
        {"name": "abc2", "arch": "power9"},
    ]


def test_node_parser_error():
    f = StringIO(
        """NodeName=abc potato=123

"""
    )
    p = node_parser(f, None)
    with pytest.raises(ValueError):
        list(p)


def test_job_parser_job_array_ids():
    f = StringIO(
        """
            JobId=135 ArrayJobId=246 ArrayTaskId=3 JobName=simplescript
        """
    )
    assert list(job_parser(f, None)) == [
        {
            "job_id": "135",
            "array_job_id": "246",
            "array_task_id": "3",
            "name": "simplescript",
        },
    ]


def test_job_parser_problematic_command_on_cedar():
    f = StringIO(
        """
   JobId=45338972 JobName=40-1e-3
   UserId=some_user_3(5348975) GroupId=some_user_3(5348975) MCS_label=N/A
   Priority=1895529 Nice=0 Account=def-some_prof_cpu QOS=normal
   JobState=RUNNING Reason=None Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=19:53:38 TimeLimit=1-23:59:00 TimeMin=N/A
   SubmitTime=2022-09-22T11:09:25 EligibleTime=2022-09-22T11:09:25
   AccrueTime=2022-09-22T11:09:25
   StartTime=2022-09-22T11:31:33 EndTime=2022-09-24T11:30:33 Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2022-09-22T11:31:33 Scheduler=Backfill
   Partition=cpubase_bycore_b4 AllocNode:Sid=cedar5:15608
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=cdr579
   BatchHost=cdr579
   NumNodes=1 NumCPUs=12 NumTasks=1 CPUs/Task=12 ReqB:S:C:T=0:0:*:*
   TRES=cpu=12,mem=32G,node=1,billing=12
   Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
   MinCPUsNode=12 MinMemoryNode=32G MinTmpDiskNode=0
   Features=[broadwell|skylake|cascade] DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/project/1234567/some_user_3/treehouse/train.sh python /home/some_user_3/projects/def-some_prof/some_user_3/treehouse/main.py --config=/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/arm_config_train.py                                             --config.random_seed=40
                                            --config.agent.random_seed=40
                                            --config.environment.action_cost_scaling=1e-3
                                            #--config.agent.max_unroll_steps=
                                            #--config.total_training_episodes=
                                            #--config.agent.e_loss_coef_start=
                                            #--config.agent.learning_rate_start=
                                            #--config.agent.learning_rate_end=
                                            #--config.environment.hz=
                                            #--config.environment.steps_per_episode=150
                                            --config.path=/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/experiments/sub_experiment/2
   WorkDir=/project/1234567/some_user_3/treehouse
   StdErr=/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/experiments/sub_experiment/2.err
   StdIn=/dev/null
   StdOut=/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/experiments/sub_experiment/2.out
   Power=
   MailUser=anonymous@anonymous.ca MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT
        """
    )

    ctx = {
        "timezone": zoneinfo.ZoneInfo("America/Montreal")
    }  # avoid errors when parsing times
    D_results = list(job_parser(f, ctx))[0]
    D_ground_truth_for_some_fields = {
        "job_id": "45338972",
        "stdin": "/dev/null",
        "stdout": "/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/experiments/sub_experiment/2.out",
        "stderr": "/home/some_user_3/projects/def-some_prof/some_user_3/treehouse/experiments/sub_experiment/2.err",
    }
    for k in D_ground_truth_for_some_fields:
        assert (
            D_ground_truth_for_some_fields[k] == D_results[k]
        ), f"Pathological job on Cedar, with Command spanning over multiple lines, parsed key {k} wrong."


def test_job_parse_with_awful_job_name():
    f = StringIO(
        """
JobId=44727557 JobName=python -O main.py seed=123456  Arch.num_classes=4 Dataset=abcd Foreground=all Trainer.name=consVat VATsettings.pertur_eps=1 Constraints.Constraint=connectivity Constraints.reward_type=soft Constraints.examples=original_unlab ConstraintWeightScheduler.max_value=0.00001  RegScheduler.max_value=0.005 Trainer.save_dir=kjhfsdkjhfsd/540938kjhfsdf Data.unlabeled_data_ratio=0.97 Data.labeled_data_ratio=0.03
   UserId=some_user_4(4238742) GroupId=some_user_4(4238742) MCS_label=N/A
   Priority=662358 Nice=0 Account=def-some_prof QOS=normal
   JobState=RUNNING Reason=None Dependency=(null)
   Requeue=0 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   RunTime=09:46:45 TimeLimit=10:00:00 TimeMin=N/A
   SubmitTime=2022-09-13T21:03:51 EligibleTime=2022-09-13T21:03:51
   AccrueTime=2022-09-13T21:03:51
   StartTime=2022-09-13T22:43:22 EndTime=2022-09-14T08:43:22 Deadline=N/A
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2022-09-13T22:43:22 Scheduler=Backfill
   Partition=gpubase_bygpu_b2 AllocNode:Sid=cedar1:4279
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=cdr2570
   BatchHost=cdr2570
   NumNodes=1 NumCPUs=6 NumTasks=1 CPUs/Task=6 ReqB:S:C:T=0:0:*:*
   TRES=cpu=6,mem=16000M,node=1,billing=1,gres/gpu=1
   Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
   MinCPUsNode=6 MinMemoryNode=16000M MinTmpDiskNode=0
   Features=[p100|p100l|v100l] DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=./tmp.sh
   WorkDir=/scratch/some_user_4/some_name
   StdErr=/scratch/some_user_4/some_name/slurm-44727557.err
   StdIn=/dev/null
   StdOut=/scratch/some_user_4/some_name/slurm-44727557.out
   Power=
   TresPerNode=gres:gpu:1
   MailUser=4237489237@492378.com MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT    
    """
    )

    ctx = {
        "timezone": zoneinfo.ZoneInfo("America/Montreal")
    }  # avoid errors when parsing times
    D_results = list(job_parser(f, ctx))[0]
    D_ground_truth_for_some_fields = {
        "job_id": "44727557",
        # may God have pity on us
        "name": "python -O main.py seed=123456  Arch.num_classes=4 Dataset=abcd Foreground=all Trainer.name=consVat VATsettings.pertur_eps=1 Constraints.Constraint=connectivity Constraints.reward_type=soft Constraints.examples=original_unlab ConstraintWeightScheduler.max_value=0.00001  RegScheduler.max_value=0.005 Trainer.save_dir=kjhfsdkjhfsd/540938kjhfsdf Data.unlabeled_data_ratio=0.97 Data.labeled_data_ratio=0.03",
        "stdin": "/dev/null",
        "stdout": "/scratch/some_user_4/some_name/slurm-44727557.out",
        "stderr": "/scratch/some_user_4/some_name/slurm-44727557.err",
    }
    for k in D_ground_truth_for_some_fields:
        assert (
            D_ground_truth_for_some_fields[k] == D_results[k]
        ), f"Pathological job, with JobName having spaces, parsed key {k} wrong."
