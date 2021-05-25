
from paramiko import SSHClient, AutoAddPolicy
ssh_client = SSHClient()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
ssh_client.load_system_host_keys()
ssh_client.connect('alaingui@beluga.computecanada.ca')
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('module load python3; python3 python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.node().get()))" ')
print(ssh_stdout) #print the output of ls command

"""
Host mila-login
     User alaingui
     Hostname login.server.mila.quebec
     PreferredAuthentications publickey,keyboard-interactive
     Port 2222
     ServerAliveInterval 120
     ServerAliveCountMax 5
"""

#### this works ####

from paramiko import SSHClient, AutoAddPolicy
ssh_client = SSHClient()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
ssh_client.load_system_host_keys()
ssh_client.connect("login.server.mila.quebec", port=2222, username="alaingui")


python_cmd = "import pyslurm; import json; print(json.dumps(dict(node=pyslurm.node().get(), reservation=pyslurm.reservation().get(), job=pyslurm.job().get())))"
# cmd = 'ssh beluga \'module load python/3.8.2; python3 -c "%s" \' ' % python_cmd
cmd = 'source ${HOME}/Documents/code/venv38/bin/activate; python3 -c "%s" ' % python_cmd
print(cmd)

ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)

#### EOF ####



from paramiko import SSHClient, AutoAddPolicy
ssh_client = SSHClient()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
ssh_client.load_system_host_keys()
ssh_client.connect("beluga.computecanada.ca", username="alaingui")

python_cmd = "import pyslurm; import json; print(json.dumps(dict(node=pyslurm.node().get(), reservation=pyslurm.reservation().get(), job=pyslurm.job().get())))"
cmd = 'module load python/3.8.2; python3 -c "%s" ' % python_cmd
# cmd = 'source ${HOME}/Documents/code/venv38/bin/activate; python3 -c "%s" ' % python_cmd
print(cmd)

ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)

ssh_stdout.readlines()




import subprocess

cmd = 'ssh beluga \'module load python/3.8.2; python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.node().get()))" \' '
E = subprocess.check_output(cmd, shell=True, encoding='utf8')

"""
# this worked on 2021-05-21
ssh beluga 'module load python/3.8.2; python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.node().get()))" ' > beluga_pyslurm_node.json
"""