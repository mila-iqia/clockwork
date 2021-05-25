"""
This script is meant to be installed in ${HOME}/bin of slurm clusters
so that we can easily call it on `vesuvan` or `deepgroove` or `monitoring`.

Here is an example of the parent script that would make use of "sinfo_scraper.py"
being a script played on the cluster login node.

Note that this is NOT the documentation for the code in "sinfo_scraper.py".

    from paramiko import SSHClient, AutoAddPolicy
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.load_system_host_keys()
    ssh_client.connect("beluga.computecanada.ca", username="alaingui")

    # python_cmd = "import pyslurm; import json; print(json.dumps(dict(node=pyslurm.node().get(), reservation=pyslurm.reservation().get(), job=pyslurm.job().get())))"
    cmd = 'module load python/3.8.2; python3 ${HOME}/bin/sinfo_scraper.py '
    # cmd = 'source ${HOME}/Documents/code/venv38/bin/activate; python3 ${HOME}/bin/sinfo_scraper.py '
    print(cmd)

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)
    # print(ssh_stdout.readlines())

    import json
    E = json.loads(" ".join(ssh_stdout.readlines()))
    psl_nodes, psl_reservations, psl_jobs = (E['node'], E['reservation'], E['job'])

    # Then our local script does something by writing that info to prometheus and elasticsearch.
    # ...

"""

import pyslurm
import json
import re

def main():
    results = { 'node': pyslurm.node().get(),
                'reservation': pyslurm.reservation().get(),
                'job': pyslurm.job().get()}

    # Then we want to filter out many of the accounts from Compute Canada
    # that are not related to Mila.
    # Obviously, this is not something that we need to do if we're running
    # on the Mila cluster. Every job on the Mila cluster has account "mila".

    accounts = set(v['account'] for v in results['job'].values())
    valid_accounts = set(
        [a for a in accounts if re.match(r".*bengio.*", a)] + ["mila"]
    )
    results['job'] = dict((k, v) for (k, v) in results['job'] if v['account'] in valid_accounts)

    # At this point, `results` contains the values that we want to return.
    # This does not mean that have done all the massaging of the data that we want to do.
    # Far from it. We will be doing plenty more in the parent script that calls "sinfo_scraper.py".
    # We have only filtered out the job entries that are not related to Mila,
    # and we did this in order to save on bandwidth.

    # We print results because the parent script will retrieve them as stdout.
    print(json.dumps(results))

if __name__ == "__main__":
    main()
