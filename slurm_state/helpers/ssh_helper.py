import os

from paramiko import SSHClient, AutoAddPolicy, ssh_exception, RSAKey


def open_connection(hostname, username, ssh_key_path, port=22):
    """
    If successful, this will connect to the remote server and
    the value of self.ssh_client will be usable.
    Otherwise, this will set self.ssh_client=None or it will quit().
    """

    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.load_system_host_keys()
    assert os.path.exists(
        ssh_key_path
    ), f"Error. The absolute path given for ssh_key_path does not exist: {ssh_key_path} ."
    pkey = RSAKey.from_private_key_file(ssh_key_path)

    # The call to .connect was seen to raise an exception now and then.
    #     raise AuthenticationException("Authentication timeout.")
    #     paramiko.ssh_exception.AuthenticationException: Authentication timeout.
    # When it happens, we should simply give up on the attempt
    # and log the error to stdout.
    try:
        # For some reason, we really need to specify which key_filename to use.
        ssh_client.connect(
            hostname, username=username, port=port, pkey=pkey, look_for_keys=False
        )
        print(f"Successful SSH connection to {username}@{hostname} port {port}.")
    except ssh_exception.AuthenticationException as inst:
        print(f"Error in SSH connection to {username}@{hostname} port {port}.")
        print(type(inst))
        print(inst)
        # set the ssh_client to None as a way to communicate
        # to the parent that we got into trouble
        ssh_client = None
    except Exception as inst:
        print(f"Error in SSH connection to {username}@{hostname} port {port}.")
        print(type(inst))
        print(inst)
        ssh_client = None

    return ssh_client


def launch_slurm_command(command, hostname, username, ssh_key_filename, port=22):
    """
    Launch a Slurm command through SSH and retrieve its response.

    Parameters:
        command             The Slurm command to launch through SSH
        hostname            The hostname used for the SSH connection to launch the Slurm command
        username            The username used for the SSH connection to launch the Slurm command
        ssh_key_filename    The name of the private key in .ssh folder used for the SSH connection to launch the Slurm command
        port                The port used for the SSH connection to launch the sinfo command
    """
    # Print the command to use
    print(f"The command launched through SSH is:\n{command}")

    # Check the given SSH key
    assert ssh_key_filename, "Missing ssh_key_filename from config."

    # Now this is the private ssh key that we are using with Paramiko.
    ssh_key_path = os.path.join(os.path.expanduser("~"), ".ssh", ssh_key_filename)

    # Connect through SSH
    try:
        ssh_client = open_connection(
            hostname, username, ssh_key_path=ssh_key_path, port=port
        )
    except Exception as inst:
        print(
            f"Error. Failed to connect to {hostname} to launch the command:\n{command}"
        )
        print(inst)
        return []

    # If a connection has been established
    if ssh_client:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(command)

        # We should find a better option to retrieve stderr
        """
            response_stderr = "".join(ssh_stderr.readlines())
            if len(response_stderr):
                print(
                    f"Stderr in sinfo call on {hostname}. This doesn't mean that the call failed entirely, though.\n{response_stderr}"
                )
            """
        stdout = ssh_stdout.readlines()
        ssh_client.close()
        return stdout

    else:
        print(
            f"Error. Failed to connect to {hostname} to make the call. Returned `None` but no exception was thrown."
        )

    # If no SSH connection has been established, raise an exception
    raise Exception(
        f"No SSH connection has been established while trying to run {command}."
    )
