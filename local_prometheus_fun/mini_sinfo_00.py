import time
import json
import re

import numpy as np
from prometheus_client import start_http_server
from prometheus_client import Enum, Summary, Gauge

# https://docs.paramiko.org/en/stable/api/client.html
from paramiko import SSHClient, AutoAddPolicy


class SinfoManager:

    LD_cluster_desc = [
        {"name": "beluga",
         "cmd" : 'module load python/3.8.2; python3 ${HOME}/bin/sinfo_scraper.py ',
         "hostname": "beluga.computecanada.ca",
         "username": "alaingui",
         "port": 22 },
        {"name": "mila",
         "cmd" : 'source ${HOME}/Documents/code/venv38/bin/activate; python3 ${HOME}/bin/sinfo_scraper.py ',
         "hostname": "login.server.mila.quebec",
         "username": "alaingui",
         "port": 2222 }
    ]

    def __init__(self):
        pass

    def open_connections(self):
        L_ssh_clients = []
        for e in self.LD_cluster_desc:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.load_system_host_keys()
            ssh_client.connect(e["hostname"], username=e["username"], port=e["port"])
            L_ssh_clients.append(ssh_client)
        self.L_ssh_clients = L_ssh_clients

    def close_connections(self):
        """
        No need to keep those connections open between polling intervals.
        Prometheus is set for 30 seconds intervals, but this seems aggressive
        when it comes to Compute Canada clusters.
        We'd rather use 5 minutes intervals and close the connections each time.
        """
        for ssh_client in self.L_ssh_clients:
            ssh_client.close()

    def fetch_data(self):

        for (ssh_client, D_cluster_desc) in zip(self.L_ssh_clients, self.LD_cluster_desc):
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

        #    self.node_states_manager[        D_cluster_desc["name"] ].update(psl_nodes)
        #    self.reservation_states_manager[ D_cluster_desc["name"] ].update(psl_reservations)
        #    self.node_states_manager[        D_cluster_desc["name"] ].update(psl_jobs)


class NodeStatesManager:
    
    # Slurm States
    slurm_node_states = [ "allocated", "completing", "idle", "maint", "mixed", "perfctrs", "power_up", "reserved" ]
    slurm_useless_states = [ "reboot", "down", "drained", "draining", "fail", "failing", "future", "power_down", "unknown" ]
    # Not built-in state
    slurm_useless_states.append('not_responding')

    def __init__(self, cluster_name):

        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name

        prom_node_states = Enum('slurm_node_states', 'States of nodes', states=NodeStates.slurm_node_states, labelnames=['name'])




    def update(self, psl_nodes_info: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_nodes_info`.
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