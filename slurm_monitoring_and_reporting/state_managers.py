

import os
import time
import json
import re
from datetime import datetime
from collections import defaultdict

from prometheus_client import Enum, Summary, Gauge

import slurm_monitoring_and_reporting
from slurm_monitoring_and_reporting.common import (extract_mila_user_account_from_job_data, )


class NodeStatesManager:
    
    # Slurm States
    slurm_node_states = [ "allocated", "completing", "idle", "maint", "mixed", "perfctrs", "power_up", "reserved" ]
    slurm_useless_states = [ "reboot", "down", "drained", "draining", "fail", "failing", "future", "power_down", "unknown" ]
    # Not built-in state
    slurm_useless_states.append('not_responding')

    def __init__(self, cluster_name, endpoint_prefix):

        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name
        self.endpoint_prefix = endpoint_prefix
        #prom_node_states = Enum('slurm_node_states', 'States of nodes', states=NodeStates.slurm_node_states, labelnames=['name'])

    def update(self, psl_nodes: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_nodes`.
        """
        pass

class ReservationStatesManager:
    def __init__(self, cluster_name, endpoint_prefix):
        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name
        self.endpoint_prefix = endpoint_prefix

    def update(self, psl_reservations: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_reservations`.
        """
        pass

class JobStatesManager:

    # slurm_job_states = []
    # This could be a premature pre-processing for Grafana.
    # It's not clean to inject too much Grafana-related concerns
    # at the Prometheus endpoint, but it's not harmful either.
    # It just feels like we shouldn't be concerned with visualization
    # at this stage of the pipeline.
    # TODO : See if this can be achieved another way in Grafana.
    slurm_job_states_color = {
        "failed" : 0, # Red
        "pending" : 5, # Orange
        "running" : 10  # Green
    }

    def __init__(self, cluster_name:str, endpoint_prefix: str, D_cluster_desc: dict):
    
        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name

        # These are just lists of strings that we will match against.
        # Look at the cluster configuration to see examples.
        self.slurm_login_nodes = D_cluster_desc["slurm_login_nodes"]
        self.slurm_partitions = D_cluster_desc["slurm_partitions"]

        # The prometheus metrics are tracked by these values.
        self.job_state_counter = Gauge(endpoint_prefix + 'slurm_job_states', cluster_name + ' Slurm Job States', labelnames=['name'])
        self.login_node_counter = Gauge(endpoint_prefix + 'slurm_login_nodes', cluster_name + ' Slurm Login Nodes', labelnames=['name'])
        self.partition_counter = Gauge(endpoint_prefix + 'slurm_partitions', cluster_name + ' Slurm Partitions', labelnames=['name'])

        self.clear_prometheus_metrics()

    def clear_prometheus_metrics(self):
        # reset the gauges
        self.job_state_counter._metrics.clear()
        self.login_node_counter._metrics.clear()
        self.partition_counter._metrics.clear()

    def update(self, psl_jobs: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by argument `psl_jobs`.
        """
        self.clear_prometheus_metrics()

        utc_now = datetime.utcnow()
        for (job_id, job_data) in psl_jobs.items():
            job_state = job_data["job_state"].lower()

            # Some fields will be added to `job_state`
            # to make it more informative. These things
            # end up in ElasticSearch but they are not
            # found in the Prometheus metrics.
            #
            # At the current time, we have not connected
            # any ElasticSearch component to this script.
            # TODO : Integrate ElasticSearch in here.

            # Infer the actual account of the person, instead
            # of having all jobs belong to "mila".
            job_data['mila_user_account'] = extract_mila_user_account_from_job_data(job_data)


            # gyom : unsure why this is necessary
            #if job_state not in self.slurm_job_states:
            #    self.slurm_job_states.append(job_state)
        
            job_data['timestamp'] = utc_now
            # Boolean for state, only for Grafana colors.
            # See comment in header of JobStatesManager class.
            if job_state in self.slurm_job_states_color.keys():
                job_data['job_state_code'] = self.slurm_job_states_color[job_state]

            # interacts with prometheus
            self.job_state_counter.labels(name=job_state).inc()

            # Login node counters
            alloc_node = job_data['alloc_node'].split('.')[0]
            # Don't count compute nodes which are sometimes used to submit
            if alloc_node in self.slurm_login_nodes:
                # interacts with prometheus
                self.login_node_counter.labels(name=alloc_node).inc()

            # Partition counter
            if job_data['partition'] in self.slurm_partitions:
                # interacts with prometheus
                self.partition_counter.labels(name=job_data['partition']).inc()

            # TODO : Put the ElasticSearch thing here.

