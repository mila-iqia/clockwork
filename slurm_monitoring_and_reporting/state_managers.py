

import os
import time
import json
import re
from datetime import datetime
from collections import defaultdict
from elasticsearch import Elasticsearch

from prometheus_client import Enum, Summary, Gauge

import slurm_monitoring_and_reporting
from slurm_monitoring_and_reporting.common import (extract_mila_user_account_from_job_data, messy_ugly_analyze_node_state, messy_ugly_analyze_gpu_gres)


class NodeStatesManager:
    """
    All the node states listed in `slurm_usable_node_states` and `slurm_useless_node_states` are going to be counted
    and reported to Prometheus.
    However, CPUs get only 4 states counted and reported.
    """

    # When nodes aren't found in any reservation
    # (i.e. when they're available for Mila students),
    # we'll enter the following value.
    default_reservation_when_missing = "None"

    # Slurm States
    slurm_usable_node_states = [ "allocated", "completing", "idle", "maint", "mixed", "perfctrs", "power_up", "reserved" ]
    slurm_useless_node_states = [ "reboot", "down", "drained", "draining", "fail", "failing", "future", "power_down", "unknown" ]
    # Not built-in state
    slurm_useless_node_states.append('not_responding')
    # All states
    slurm_node_states = slurm_usable_node_states + slurm_useless_node_states

    # States for CPU/GPU.
    # TODO : I think that there are more states than that in slurm.
    #        However, there is a projection done by `common.messy_ugly_analyze_node_state`
    #        unto those 4 states.
    #        Since `messy_ugly_analyze_node_state` is put into question,
    #        it makes sense to rethink this `slurm_pu_states` constant here.
    #        Do we really want only 4 states?
    slurm_pu_states=[ "alloc", "idle", "drain", 'total' ]

    # See comment about `slurm_job_states_color` also being
    # at the wrong place in the pipeline.
    # This is for Grafana, and it shouldn't be here.
    # TODO : Rethink this properly in design doc.
    slurm_node_states_color = {
        "down" : 0, # Red
        "drained" : 5, # Orange foncé
        "draining" : 10  # Green
    }


    def __init__(self, cluster_name, endpoint_prefix, D_cluster_desc: dict,
        D_elasticsearch_config: dict, elasticsearch_client:Elasticsearch=None):

        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name
        self.endpoint_prefix = endpoint_prefix

        # any node that belongs to this will be filtered out
        self.slurm_ignore_partitions = set(D_cluster_desc['slurm_ignore_partitions'])

        self.D_elasticsearch_config = D_elasticsearch_config
        self.elasticsearch_client = elasticsearch_client


        # CPU/GPU state counters
        self.cpu_state_counters = {}
        self.gpu_state_counters = {}
        for pu_state in NodeStatesManager.slurm_pu_states:
            self.cpu_state_counters[pu_state] = Gauge('slurm_cpus_' + pu_state, pu_state + ' CPUs', labelnames=[ 'reservation' ])
            self.gpu_state_counters[pu_state] = Gauge('slurm_gpus_' + pu_state, pu_state + ' GPUs', labelnames=[ 'type', 'reservation' ])

        self.prom_node_states = Enum('slurm_node_states', 'States of nodes', states=NodeStatesManager.slurm_node_states, labelnames=['name'])

        self.clear_prometheus_metrics()

    def clear_prometheus_metrics(self):
        # reset the gauges
        #     prom_node_states
        #     cpu_state_counters
        #     gpu_state_counters
        #
        #self.job_state_counter._metrics.clear()
        #self.login_node_counter._metrics.clear()
        #self.partition_counter._metrics.clear()
        pass

    def update(self, psl_reservations: dict, psl_nodes: dict):
        """
        Update all your counters and gauges based on the latest readout
        given by arguments `psl_reservations` and `psl_nodes`.

        The only reason why we care about `psl_reservations` is to add
        a field "reservation" to the information that we report about nodes.
        When the nodes are not reserved, they will be maked
            node_data['reservation'] = "None"
        which will be a way to identify the majority of the nodes
        available to Mila students.
        """

        # This is an operation that takes linear time in the
        # number of nodes to build a lookup table, in order to
        # avoid something that costs the square of the number of nodes.
        # Warning: We have the hidden assumption that a given node
        # can only be in one reservation at a time. This seems true enough,
        # and even when it isn't, it sounds like a reasonable approxiation.
        unix_now = time.time()
        node_name_to_resv_name = {}
        for (resv_name, resv_desc) in psl_reservations.items():
            # `resv_name` is the answer, and now we must find the question that maps to it
            if resv_desc['start_time'] <= unix_now <= resv_desc['end_time'] :
                if 'node_list_simplified' in resv_desc:
                    for node_name in resv_desc['node_list_simplified']:
                        node_name_to_resv_name[node_name] = resv_name



        # accumulate over elements of psl_nodes
        # and bulk commit to elasticsearch after
        es_nodes_body = []
        
        self.clear_prometheus_metrics()

        utc_now = datetime.utcnow()
        for (node_name, node_data) in psl_nodes.items():
            #node_state = node_data["job_state"].lower()        
            
            for p in node_data['partitions']:
                if p in self.slurm_ignore_partitions:
                    continue

            

            node_data["reservation"] = node_name_to_resv_name.get(node_name, self.default_reservation_when_missing)

            node_data['state'] = messy_ugly_analyze_node_state(node_data['state'])


            # Grafana wants UTC
            node_data['timestamp'] = utc_now

            # Boolean for state, only for Grafana colors
            if node_data['state'] in self.slurm_node_states_color:
                node_data['grafana_helpers'] = {
                        'job_state_color': self.slurm_node_states_color[node_data['state']]
                }

            if node_data.get('reason_time', None) is not None:
                node_data['reason_time_str'] = datetime.fromtimestamp(node_data['reason_time']).astimezone().strftime('%Y-%m-%dT%H:%M:%S %Z')

            # Add Elastic Search action for each node.
            es_nodes_body.append({'index': {'_id': node_data['node_name']}})            
            es_nodes_body.append(node_data)

            # Save in dict. Note that all the many possible node states are counted.
            # This is not a projection down to 4 node states.
            self.prom_node_states.labels(name=node_name).state(node_data['state'])


            ##############################################
            # CPUs
            # Keep track of idle CPUs

            # An example of node_data fields would be {"cpus": 80, "alloc_cpus": 32, "err_cpus": 0}.
            # In that case, we'd want to add the field "idle_cpus" with count 80-32=48.
            # As for counters,
            #     - The "total" is 80 cpus.
            #     - The "alloc" is 32 cpus.
            #     - The "drain" is 0 cpus. This measurement is not very well named.
            #     - The "idle" is the idle_cpus if the state is good,
            #       but otherwise the idle_cpus are added to "drain".
            #
            # The word "drain" is really being used a catchcall category for errors.

            node_data['idle_cpus'] = node_data['cpus'] - node_data['err_cpus']
            self.cpu_state_counters['total'].labels(reservation=node_data["reservation"]).inc(node_data['cpus'])
            self.cpu_state_counters['alloc'].labels(reservation=node_data["reservation"]).inc(node_data['alloc_cpus'])
            self.cpu_state_counters['drain'].labels(reservation=node_data["reservation"]).inc(node_data['err_cpus'])
            if node_data['state'] not in NodeStatesManager.slurm_useless_node_states:
                self.cpu_state_counters['idle'].labels(reservation=node_data["reservation"]).inc(node_data['idle_cpus'])
            else:
                # TODO : Whoa! This is NOT a node being drained. It could be in any number of problematic states.
                #        We're just not keeping track of the problematics states.
                self.cpu_state_counters['drain'].labels(reservation=node_data["reservation"]).inc(node_data['idle_cpus'])


            # If the 'gres' field exists, and provided it's a list with at least one element.
            if node_data.get('gres', []):
                node_data['gpus'] = messy_ugly_analyze_gpu_gres(node_data['gres'], node_data['gres_used'])
                
                # Loop on sanitized gpus and set counters
                for gpu_name, gpu_counts in node_data['gpus']:
                    # gpu_name described the name of a product from nvidia (ex : "rtx8000", "m40", "k80")
                    # gpu_counts is a dict with keys ['total', 'alloc']

                    self.gpu_state_counters['total'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'])
                    self.gpu_state_counters['alloc'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['alloc'])
                    # Test state: if node is available/mixed and a least 1 cpu is avail, gres are idle otherwise drain
                    # TODO : The comment from previous line was copied as it was in "sinfo.py".
                    #        We're not sure how good of an idea that was.
                    #        This is yet another of those situations where it's worth a discussion with the group.
                    if node_data['state'] not in NodeStatesManager.slurm_useless_states and node_data['idle_cpus']>1:
                        self.gpu_state_counters['idle'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'] - gpu_counts['alloc'])
                    else:
                        self.gpu_state_counters['drain'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'] - gpu_counts['alloc'])





# class ReservationStatesManager:
#     def __init__(self, cluster_name, endpoint_prefix, D_cluster_desc: dict,
#         D_elasticsearch_config: dict, elasticsearch_client:Elasticsearch=None):
#         assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
#         self.cluster_name = cluster_name
#         self.endpoint_prefix = endpoint_prefix

#         # D_cluster_desc

#         self.D_elasticsearch_config = D_elasticsearch_config
#         self.elasticsearch_client = elasticsearch_client

#     def update(self, psl_reservations: dict):
#         """
#         Update all your counters and gauges based on the latest readout
#         given by argument `psl_reservations`.
#         """
#         pass

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

    # Jobs have certain fields that contain dates.
    # For each of those fields, we'll add an extra one that's easier to display.
    # It will have the same key followed by the "_str" suffix.
    # We are not overwriting the original value.
    job_date_fields = [ 'submit_time', 'start_time', 'end_time', 'eligible_time']


    def __init__(self,
        cluster_name:str, endpoint_prefix: str, D_cluster_desc: dict,
        D_elasticsearch_config: dict, elasticsearch_client:Elasticsearch=None):
    
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

        self.D_elasticsearch_config = D_elasticsearch_config
        self.elasticsearch_client = elasticsearch_client

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

        # accumulate over elements of psl_jobs
        # and bulk commit to elasticsearch after
        es_jobs_body = []

        utc_now = datetime.utcnow()
        for (job_id, job_data) in psl_jobs.items():
            job_state = job_data["job_state"].lower()

            # Some fields will be added to `job_state`
            # to make it more informative. These things
            # end up in ElasticSearch but they are not
            # found in the Prometheus metrics.

            # Infer the actual account of the person, instead
            # of having all jobs belong to "mila".
            job_data['mila_user_account'] = extract_mila_user_account_from_job_data(job_data)
            # Very useful for later when we untangle the sources in the plots.
            job_data['cluster_name'] = self.cluster_name

            # Guillaume says : I'm unsure why Quentin does this.
            #if job_state not in self.slurm_job_states:
            #    self.slurm_job_states.append(job_state)
        
            # Quentin wrote that Grafana wanted UTC.
            job_data['timestamp'] = utc_now
            # Create display time for convenience.
            for key in self.job_date_fields:
                job_data[key + '_str'] = datetime.fromtimestamp(job_data[key]).astimezone().strftime('%Y-%m-%dT%H:%M:%S %Z')
                # Maybe add a UTC version here too?

            # Boolean for state, only for Grafana colors.
            # See comment in header of JobStatesManager class.
            if job_state in self.slurm_job_states_color.keys():
                job_data['grafana_helpers'] = {
                    'job_state_color': self.slurm_job_states_color[job_state]
                }

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

            # ElasticSearch thing here.
            # The current understanding that we have about how ElasticSearch
            # bulk updates work is that it's normal to have a sequence of
            # two types of entries interweaved:
            #     one meta, one content, one meta, one content.

            # add ElasticSearch action for each job
            es_jobs_body.append({'index': {'_id': int(job_id)}})
            # full body
            es_jobs_body.append(job_data)

        print(f"Want to bulk commit {len(es_jobs_body)} values to ElasticSearch.")
        # Send bulk update for ElasticSearch.
        self.elasticsearch_client.bulk(
            index=self.D_elasticsearch_config['jobs_index'],
            body=es_jobs_body, timeout=self.D_elasticsearch_config['timeout'])
        print("Done with commit to ElasticSearch.")

        # TODO : Add a mongodb component as well?