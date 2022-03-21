"""
Tests for slurm_state.helpers.gpu_helper
"""

import pytest

from slurm_state.helpers.gpu_helper import *


def test_get_gres_dict():
    """
    Test the set up of the dictionary obtained by parsing the Gres field of a
    Slurm node description.
    """
    assert get_gres_dict("(null)") == {}
    assert get_gres_dict("gpu:rtx8000:4(S:0-1)") == {
        "name": "rtx8000",
        "number": 4,
        "associated_sockets": "0-1"
    }
    assert get_gres_dict("gpu:v100:5") == {
        "name": "v100",
        "number": 5
    }
    assert get_gres_dict("gpu:rtx8000:bla(S:0-1)") == {}
    assert get_gres_dict("ab:rtx8000:4") == {}
    assert get_gres_dict("aa:bbbb") == {}

def test_cw_gpu_name():
    """
    Test the retrieving of a common name for the GPU, because Mila and
    ComputeCanada clusters do not use the same Slurm description conventions.

    For now, the function use the information of the fields "AvailableFeatures"
    and "Gres" of the Slurm report describing a node on the Mila cluster to
    associate its GPU name following the convention of ComputeCanada.
    """

    # Case of an untransformed GPU name
    assert get_cw_gpu_name("rtx8000", "x86_64,turing,48gb") == "rtx8000"

    # Case of v100 becoming v100l
    assert get_cw_gpu_name("v100", "aaaa,test,32gb") == "v100l"

    # Case of v100 staying v100
    assert get_cw_gpu_name("v100", "aaaa,test,16gb") == "v100"

    # Case of features that do not match the format used by the function
    assert get_cw_gpu_name("v100", "randomunformattedfield") == "v100"

    # Case of an empty GPU name
    assert get_cw_gpu_name("", "aaaa,test,16gb") == ""

    # Case of an empty "features" field
    assert get_cw_gpu_name("t4", "") == "t4"


def test_get_cw_gres_description():
    """
    Test the creation of a dictionary presenting the GPU information of the node
    from the 'Gres' and 'AvailableFeatures' fields of the Slurm report.
    """
    # Case of an untransformed GPU name, with two associated sockets
    assert get_cw_gres_description("gpu:rtx8000:8(S:0-1)", "x86_64,turing,48gb") == {
        "cw_name": "rtx8000",
        "name": "rtx8000",
        "number": 8,
        "associated_sockets": "0-1"
    }

    # Case of p100 becoming p100l, with one associated socket
    assert get_cw_gres_description("gpu:p100:4(S:0)", "aaaa,test,16gb") == {
        "cw_name": "p100l",
        "name": "p100",
        "number": 4,
        "associated_sockets": "0"
    }

    # Case of p100 staying p100, with no associated socket
    assert get_cw_gres_description("gpu:p100:2", "aaaa,test,12gb") == {
        "cw_name": "p100",
        "name": "p100",
        "number": 2
    }

    # Case of features that do not match the format used by the function with
    # two associated sockets
    assert get_cw_gres_description("gpu:v100:6(S:0-1)", "randomunformattedfield") == {
        "cw_name": "v100",
        "name": "v100",
        "number": 6,
        "associated_sockets": "0-1"
    }

    # Case of an empty 'Gres' field
    assert get_cw_gres_description(None, "aaaa,test,16gb") == {}

    # Case of an empty 'AvailableFeatures' field
    assert get_cw_gres_description("t4", "") == {}
