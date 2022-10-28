import pytest
from io import StringIO
from slurm_state.sacct_access import (
    fetch_data_with_sacct_on_remote_clusters,
    open_connection,
)

from slurm_state.config import get_config

# because we'll mock that class
from paramiko import SSHClient

from unittest.mock import patch

# We are not going to be able to test
#     slurm_state.sacct_access.open_connection(
#         hostname, username, ssh_key_path, port=22)
# because it requires a SSH connection to a remote host.
# Moreover, we need to mock this function because
# it is used inside of `fetch_data_with_sacct_on_remote_clusters`,
# which is definitely a function that we need to test.


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "narval")
)
def test_mocked_ssh_open_connection(monkeypatch, cluster_name):
    """
    This test is more of a demonstration that the mocking mechanics work.
    The actual testing of code for Clockwork comes after.
    We can also use this as a starting template for actual tests.

    Note that we are not using `cluster_name` anywhere here,
    but having it positioned as second argument documents
    the fact that this is where it will belong in actual tests,
    which is not obvious with two decorators.
    """

    def mock_exec_command(self, remote_cmd):
        stdin = StringIO("")
        stdout = StringIO(f"hello {cluster_name}")
        stderr = StringIO(f"world {cluster_name}")
        return (stdin, stdout, stderr)

    monkeypatch.setattr(SSHClient, "connect", lambda *args, **kwargs: None)
    monkeypatch.setattr(SSHClient, "exec_command", mock_exec_command)

    ssh_client = open_connection(
        hostname="some_fake_hostname",
        username="some_fake_username",
        ssh_key_path=".",
        port=22,
    )

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "this can be any string"
    )

    response_stdin = "\n".join(ssh_stdin.readlines())
    response_stdout = "\n".join(ssh_stdout.readlines())
    response_stderr = "\n".join(ssh_stderr.readlines())

    assert response_stdin == ""
    assert response_stdout == f"hello {cluster_name}"
    assert response_stderr == f"world {cluster_name}"


@pytest.mark.parametrize(
    "cluster_name", ("mila", "cedar", "graham", "beluga", "narval")
)
def test_mocked_sacct(monkeypatch, cluster_name):
    """ """

    # Some manual offset for cedar being in British Columbia.
    time_offset = 3 * 60 * 60 if cluster_name == "cedar" else 0.0

    # print('get_config("clusters")[cluster_name]')
    # print(get_config("clusters")[cluster_name])

    #
    # get_config("clusters")[cluster_name]
    # {'allocations': ['def-patate-rrg', 'def-pomme-rrg', 'def-cerise-rrg', 'def-citron-rrg'],
    #  'sacct_path': '/opt/software/slurm/bin/sacct',
    #  'sacct_ssh_key_filename': 'id_clockwork'}

    L_job_ids = ["2127660188", "43284723"]
    account = "mila" if cluster_name == "mila" else "rrg-bengioy-ad_gpu"

    # Yes, we have obtained those timestamps manually with a web site that does
    # the conversion. The alternative is to just to reuse/duplicate the very function from
    # scontrol_parser.py that converts time, and that wouldn't be much of a unit test
    # if it's too circular.
    expected_LD_partial_slurm_jobs = [
        {
            "account": account,
            "uid": "2127660188",
            "username": "aaa.bbb",
            "job_id": "2281126",
            "array_job_id": "2280887",
            "array_task_id": "0",
            "job_state": "COMPLETED",
            "name": "train",
            "submit_time": 1663530134.0 + time_offset,
            "start_time": 1663533734.0 + time_offset,
            "end_time": 1663562886.0 + time_offset,
        },
        {
            "account": account,
            "uid": "43284723",
            "username": "manfred",
            "job_id": "2281130",
            "job_state": "OUT_OF_MEMORY",
            "name": "resnet_R2S",
            "submit_time": 1663684934.0 + time_offset,
            "start_time": 1663688534.0 + time_offset,
            "end_time": 1663695720.0 + time_offset,
        },
    ]

    # careful about new lines and spacing in this string because it affects the csv parsing
    expected_sacct_output = f"""Account|UID|User|JobIDRaw|JobID|JobName|State|Submit|Start|End|
{account}|2127660188|aaa.bbb|2281126|2280887_0|train|COMPLETED|2022-09-18T15:42:14|2022-09-18T16:42:14|2022-09-19T00:48:06| 
{account}|43284723|manfred|2281130|2281130|resnet_R2S|OUT_OF_MEMORY|2022-09-20T10:42:14|2022-09-20T11:42:14|2022-09-20T13:42:00|"""
    # Let's not use that part of the handcrafted data for now. Too much to write.
    # And you'll have to add back "submit_time" in there.
    # """
    # {account}|2127660188|aaa.bbb|2281127|2280887_1|train|TIMEOUT|2022-09-18T16:42:14|2022-09-20T02:02:33|
    # {account}|2127660188|aaa.bbb|2281128|2280887_2|train|COMPLETED|2022-09-18T16:42:14|2022-09-19T01:08:41|
    # {account}|2127660188|aaa.bbb|2281129|2280887_3|train|TIMEOUT|2022-09-18T16:42:14|2022-09-20T02:02:33|
    # {account}|2127660188|aaa.bbb|2281130|2280887_4|train|COMPLETED|2022-09-18T16:42:14|2022-09-19T00:26:22|
    # """

    # make it more realistic by having this message show up on CC clusters
    expected_sacct_stderr = (
        ""
        if cluster_name == "mila"
        else "/usr/bin/id: cannot find name for group ID 13200126"
    )

    # Hmmm, this doesn't feel like it's the correct way to mock things
    # but it works great.
    class E:
        def exec_command(remote_cmd):
            return (
                StringIO(""),
                StringIO(expected_sacct_output),
                StringIO(expected_sacct_stderr),
            )

        def close():
            return

    monkeypatch.setattr(
        "slurm_state.sacct_access.open_connection", lambda *vargs, **kwargs: E
    )

    ## We really thought this would work as intended, but it doesn't.
    # f = lambda *vargs, **kwargs: 1.0
    # setattr(f, "exec_command", lambda self, remote_cmd: (StringIO(""), StringIO(expected_sacct_output), StringIO(expected_sacct_stderr)))
    # monkeypatch.setattr("slurm_state.sacct_access.open_connection", f)
    #
    ## And neither does this.
    # def mock_exec_command(self, remote_cmd):
    #     stdin = StringIO("")
    #     stdout = StringIO(expected_sacct_output)
    #     stderr = StringIO(expected_sacct_stderr)
    #     return (stdin, stdout, stderr)
    # monkeypatch.setattr(SSHClient, "connect", lambda *args, **kwargs: None)
    # monkeypatch.setattr(SSHClient, "exec_command", mock_exec_command)

    LD_partial_slurm_jobs = fetch_data_with_sacct_on_remote_clusters(
        cluster_name=cluster_name, L_job_ids=L_job_ids
    )

    assert len(expected_LD_partial_slurm_jobs) == len(LD_partial_slurm_jobs)
    for a, b in zip(expected_LD_partial_slurm_jobs, LD_partial_slurm_jobs):
        assert a == b
