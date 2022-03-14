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
        """NodeName=abc1 Arch=x86_64

NodeName=abc2 Arch=power9

"""
    )
    assert list(node_parser(f, None)) == [
        {"name": "abc1", "arch": "x86_64"},
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
