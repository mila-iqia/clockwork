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
