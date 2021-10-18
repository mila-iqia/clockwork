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

from collections import defaultdict
import pyslurm
import json
import re
import time


def add_node_list_simplified(psl_reservations: dict):
    """
    dicts returned by `pyslurm.reservation().get()`
    will have an entry
        "node_list": "blg[4109,4701,5201,5303,5305,5308-5309,5501,5608-5609,5702,5803-5804,5806]"
    This is obviously not something that we'd like to parse ourselves
    since pyslurm already has a way to decode this.

    We'd just like to convert it into a list of node names
    to have compatibility with `pyslurm.node().get()`.

    Since we're going to use pyslurm for this, it makes
    sense to do it in the scraper script (i.e. here)
    because the Prometheus endpoint might not be running
    on a machine where pyslurm is installed (nor should it
    be required).

    The side-effect of this function will be simply to
    add a field "node_list_simplified" that will contain
    the values
        "node_list_simplified": ["blg4109","blg4701","blg5201","blg5303","blg5305","blg5308","blg5309","blg5501","blg5608","blg5609","blg5702","blg5803","blg5804","blg5806]
    """
    for resv_desc in psl_reservations.values():
        hl = pyslurm.hostlist()  # we need to involve pyslurm in this process
        hl.create(resv_desc["node_list"])
        # modify in place
        resv_desc["node_list_simplified"] = [e.decode("UTF-8") for e in hl.get_list()]


def main():
    results = {
        "node": pyslurm.node().get(),
        "reservation": pyslurm.reservation().get(),
        "job": pyslurm.job().get(),
    }

    add_node_list_simplified(results["reservation"])

    # We decided to avoid doing this approach, but let's keep the code around
    # for just a little while.
    # results['node_name_to_resv_names'] = get_node_name_to_resv_names(results['reservation'])

    # Then we want to filter out many of the accounts from Compute Canada
    # that are not related to Mila.
    # Obviously, this is not something that we need to do if we're running
    # on the Mila cluster. Every job on the Mila cluster has account "mila".

    accounts = set(v["account"] for v in results["job"].values())
    valid_accounts = set([a for a in accounts if re.match(r".*bengio.*", a)] + ["mila"])
    results["job"] = dict(
        (k, v) for (k, v) in results["job"].items() if v["account"] in valid_accounts
    )

    # At this point, `results` contains the values that we want to return.
    # This does not mean that have done all the massaging of the data that we want to do.
    # Far from it. We will be doing plenty more in the parent script that calls "sinfo_scraper.py".
    # We have only filtered out the job entries that are not related to Mila,
    # and we did this in order to save on bandwidth.

    # We print results because the parent script will retrieve them as stdout.
    print(json.dumps(results))


if __name__ == "__main__":
    main()

    """
    rsync -av ${HOME}/Documents/code/slurm_monitoring_and_reporting/misc/sinfo_scraper.py mila-login:bin

    rsync -av ${HOME}/Documents/code/slurm_monitoring_and_reporting/misc/sinfo_scraper.py beluga:bin
    """


###############################################################
# The path not taken.
#   This code works fine, but there's a better way to do things
#   cleanly. Let's keep it around just in case we need it.
#   Probably safe to delete it after 2021-05-31 plus two months.
###############################################################


def get_node_name_to_resv_names(psl_reservations: dict):
    """
    dicts returned by `pyslurm.reservation().get()`
    will have an entry
        "node_list": "blg[4109,4701,5201,5303,5305,5308-5309,5501,5608-5609,5702,5803-5804,5806]"
    This is obviously not something that we'd like to parse ourselves
    since pyslurm already has a way to decode this.

    We'd just like to convert it into a list of node names
    to have compatibility with `pyslurm.node().get()`.

    Since we're going to use pyslurm for this, it makes
    sense to do it in the scraper script (i.e. here)
    because the Prometheus endpoint might not be running
    on a machine where pyslurm is installed (nor should it
    be required).

    The output of this function is a dict that maps
    from node_name to resv_names. That is, it's something like
    {
        "blg4109": ["cq26-wr_gpu"],
        "blg4701": ["cq26-wr_gpu"],
        ...
    }
    It seemed appropriate to map to lists because we weren't sure
    if a given node could be part of two reservations.

    The logic in this function comes partly from the
    "sinfo.py" script in the `get_reservations()` function.
    """

    unix_now = time.time()

    node_name_to_resv_names = defaultdict(list)

    for (resv_name, resv_desc) in psl_reservations.items():
        # `resv_name` is the answer, and now we must find the question that maps to it
        if resv_desc["start_time"] <= unix_now <= resv_desc["end_time"]:

            # get hostlist
            hl = pyslurm.hostlist()
            hl.create(resv_desc["node_list"])

            # they're bytefields that need decoding
            for node_name_bytes in hl.get_list():
                node_name = node_name_bytes.decode("UTF-8")
                node_name_to_resv_names[node_name].append(resv_name)

    return node_name_to_resv_names
