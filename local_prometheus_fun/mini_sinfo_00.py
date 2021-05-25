"""
One of the main criticisms about this script is that it does something entirely in parallel,
for each cluster, and exposes everything as a single server for prometheus.

It might be worth ripping it apart to have multiple servers instead,
and to launch them separately.

Moreover, we are fetching information by ssh to remote machines,
but this wouldn't be necessary when we can access pyslurm on the local machine.
That becomes a special case (which we can solve by setting the hostname
to the local machine), but it just goes to show that we have two particular
aspects that are fused. We could imagine people over at CC running
the prometheus endpoint on our behalf, and exposing it to us.
We'll cross that bridge when we get there.
"""

import time
import json
import re

import numpy as np
from prometheus_client import start_http_server
from prometheus_client import Enum, Summary, Gauge

# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy


class SinfoManager:

    cluster_names = ["beluga", "mila"]

    DD_cluster_desc = {
        "beluga":
            {"name": "beluga",
            "cmd" : 'module load python/3.8.2; python3 ${HOME}/bin/sinfo_scraper.py ',
            "hostname": "beluga.computecanada.ca",
            "username": "alaingui",
            "port": 22 },
        "mila":
            {"name": "mila",
            "cmd" : 'source ${HOME}/Documents/code/venv38/bin/activate; python3 ${HOME}/bin/sinfo_scraper.py ',
            "hostname": "login.server.mila.quebec",
            "username": "alaingui",
            "port": 2222 }
    }

    def __init__(self):
        self.D_ssh_clients = {}
        self.D_node_states_manager = dict( (cluster_name, NodeStatesManager(cluster_name)) for cluster_name in self.cluster_names )
        self.D_reservation_states_manager = dict( (cluster_name, ReservationStatesManager(cluster_name)) for cluster_name in self.cluster_names )
        self.D_job_states_manager = dict( (cluster_name, JobStatesManager(cluster_name)) for cluster_name in self.cluster_names )

    def open_connections(self):
        self.D_ssh_clients = {}
        for name in self.cluster_names:
            e = self.DD_cluster_desc[name]
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.load_system_host_keys()
            ssh_client.connect(e["hostname"], username=e["username"], port=e["port"])
            self.D_ssh_clients[name] = ssh_client

    def close_connections(self):
        """
        No need to keep those connections open between polling intervals.
        Prometheus is set for 30 seconds intervals, but this seems aggressive
        when it comes to Compute Canada clusters.
        We'd rather use 5 minutes intervals and close the connections each time.
        """
        for name in self.cluster_names:
            self.D_ssh_clients[name].close()

    def fetch_data(self):

        for name in self.cluster_names:
            D_cluster_desc = self.DD_cluster_desc[name]
            ssh_client = self.L_ssh_clients[name]

            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(D_cluster_desc["cmd"])
            # print(ssh_stdout.readlines())
            try:
                E = json.loads(" ".join(ssh_stdout.readlines()))
                psl_nodes, psl_reservations, psl_jobs = (E['node'], E['reservation'], E['job'])
            except Exception as inst:
                print(type(inst))    # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)
                psl_nodes, psl_reservations, psl_jobs = (None, None, None)
                continue

            self.node_states_manager[name].update(psl_nodes)
            self.reservation_states_manager[name].update(psl_reservations)
            self.node_states_manager[name ].update(psl_jobs)


class NodeStatesManager:
    
    # Slurm States
    slurm_node_states = [ "allocated", "completing", "idle", "maint", "mixed", "perfctrs", "power_up", "reserved" ]
    slurm_useless_states = [ "reboot", "down", "drained", "draining", "fail", "failing", "future", "power_down", "unknown" ]
    # Not built-in state
    slurm_useless_states.append('not_responding')

    def __init__(self, cluster_name):

        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name
        #prom_node_states = Enum('slurm_node_states', 'States of nodes', states=NodeStates.slurm_node_states, labelnames=['name'])

    def update(self, psl_nodes: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_nodes`.
        """
        pass

class ReservationStatesManager:
    def __init__(self, cluster_name):
        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name

    def update(self, psl_reservations: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_reservations`.
        """
        pass

class JobStatesManager:
    def __init__(self, cluster_name):
        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name

    def update(self, psl_jobs: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_jobs`.
        """
        pass


def sinfo():

    # Reset Gauge
    job_state_counter._metrics.clear()
    login_node_counter._metrics.clear()
    partition_counter._metrics.clear()
    for pu_state in slurm_pu_states:
        cpu_state_counters[pu_state]._metrics.clear()
        gpu_state_counters[pu_state]._metrics.clear()





def run():
    port = 19998
    prom_metrics = {'request_latency_seconds': Summary('request_latency_seconds', 'Description of summary')}

    start_http_server(port)
    while True:
        process_request(prom_metrics)
        time.sleep(1)

if __name__ == "__main__":
    run()