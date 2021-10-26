from io import StringIO
from slurm_state.scontrol_parser import *


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
