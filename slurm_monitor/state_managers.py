

import os
import time
import json
import re
from datetime import datetime
from collections import defaultdict
from elasticsearch import Elasticsearch
from pymongo import UpdateOne

from prometheus_client import Enum, Summary, Gauge

import slurm_monitor
from slurm_monitor.common import (extract_username_from_job_data, messy_ugly_analyze_node_state, messy_ugly_analyze_gpu_gres)


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
    slurm_pu_states=[ "alloc", "idle", "drain", "total" ]
    # Note that "total" and "alloc" are values that are reported by slurm,
    # and the other two values are things that we make up, infer, or decide
    # to label.
    # Anything left out between the "alloc" and the "total" is deemed to be
    # either usable (so it's "idle") or to be in a bad state (i.e. "drain").
    #
    # The use of the word "drain" is potentially misleading.
    # This is a conversation that should be had over design documents.
    # It leads someone to think that we're reporting a slurm "drain" state,
    # but actually we're just electing that word to mean that the resource
    # can't be used at the moment.
    # This is part of the discussion around `common.messy_ugly_analyze_node_state`.


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
        D_elasticsearch_config: dict, elasticsearch_client:Elasticsearch=None,
        D_mongodb_config:dict={}, mongo_client=None):

        assert cluster_name in ["mila", "beluga", "graham", "cedar", "dummy"]
        self.cluster_name = cluster_name
        self.endpoint_prefix = endpoint_prefix

        # any node that belongs to this will be filtered out
        self.slurm_ignore_partitions = set(D_cluster_desc['slurm_ignore_partitions'])
        
        # We purposefully avoid storing a self copy of `D_cluster_desc`
        # to make explicit the ways in which it is being used (i.e. not much).

        self.D_elasticsearch_config = D_elasticsearch_config
        self.elasticsearch_client = elasticsearch_client

        self.D_mongodb_config = D_mongodb_config
        self.mongo_client = mongo_client

        # CPU/GPU state counters

        # There are 4x2 counters,
        #     slurm_cpus_alloc, slurm_cpus_idle, slurm_cpus_drain, slurm_cpus_total
        #     slurm_gpus_alloc, slurm_gpus_idle, slurm_gpus_drain, slurm_gpus_total
        # but those counters will internally keep other totals due to the fact that
        # the labelnames include the reservation (usually "None") and types of gpu,
        # meaning that we get a separate counter for each of
        #     reservation="None", type="k80"
        #     reservation="None", type="m40"
        #     reservation="None", type="rtx8000"
        # and so on.
        self.cpu_state_counters = {}
        self.gpu_state_counters = {}
        for pu_state in NodeStatesManager.slurm_pu_states:
            self.cpu_state_counters[pu_state] = Gauge('slurm_cpus_' + pu_state, pu_state + ' CPUs', labelnames=[ 'reservation' ])
            self.gpu_state_counters[pu_state] = Gauge('slurm_gpus_' + pu_state, pu_state + ' GPUs', labelnames=[ 'type', 'reservation' ])

        # This creates a separate individual metric for hundreds of nodes to track their state.
        self.prom_node_states = Enum('slurm_node_states', 'States of nodes', states=NodeStatesManager.slurm_node_states, labelnames=['name'])

        self.clear_prometheus_metrics()

    def clear_prometheus_metrics(self):
        # reset the gauges for prom_node_states, cpu_state_counters, gpu_state_counters
        self.prom_node_states._metrics.clear()
        for counter in list(self.cpu_state_counters.values()) + list(self.gpu_state_counters.values()):
            counter._metrics.clear()

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
        #
        # Moreover, note that these values could be cached instead of being
        # recomputed each time, but then we'd lose the time verification.
        # The cost of recomputing this each time should be minor, especially
        # since this is a function that's never going to be called more than
        # once every minute.
        # We already have to traverse all the nodes each time `update` is called
        # so that shouldn't be a problem, algorithmically-speaking.
        unix_now = time.time()
        node_name_to_resv_name = {}
        for (resv_name, resv_desc) in psl_reservations.items():
            # `resv_name` is the answer, and now we must find the question that maps to it
            if resv_desc['start_time'] <= unix_now <= resv_desc['end_time'] :
                if 'node_list_simplified' in resv_desc:
                    for node_name in resv_desc['node_list_simplified']:
                        node_name_to_resv_name[node_name] = resv_name

        # Accumulate over elements of psl_nodes
        # and bulk commit to Elastic Search at the end of `update`.
        # TODO : You know, this whole thing is not necessary.
        #        We're iterating through `(node_name, node_data) in psl_nodes.items()`
        #        and we're updating the `node_data` by writing into it.
        #        The big Elastic Search update at the end, as well as the mongodb bulk_write update,
        #        can easily be constructed from iterating through `psl_nodes.items()` again.
        #        Let's test it with mongodb and then update the Elastic Search part.
        #        Feels like Dracula (1931) with the Spanish version being strictly better shots.
        es_nodes_body = []

        self.clear_prometheus_metrics()

        utc_now = datetime.utcnow()
        for (node_name, node_data) in psl_nodes.items():

            # Write the cluster_name in node_data.
            # It's going to be useful for many things but one of the uses is that
            # it will provide unique ids for mongodb in the form of (node_name, cluster_name).
            node_data["cluster_name"] = self.cluster_name

            # Copied from "sinfo.py" assuming that we'd have good reasons
            # to want to ignore certain partitions.
            # Right now these ignored partitions seem to be related 
            # to cloud computing partitions set up at Mila temporarily.
            for p in node_data['partitions']:
                if p in self.slurm_ignore_partitions:
                    continue

            # Most of the times, "reservation" is "None", meaning
            # that the node is accessible to all Mila students
            # instead of being reserved for MLART, for example.
            node_data["reservation"] = node_name_to_resv_name.get(node_name, self.default_reservation_when_missing)

            # Since we're going to be messing up with the 'state',
            # it's a good idea to store whatever the original value was.
            # This might allow us to dig better to debug cluster issues,
            # or simply to make better opinions about what kind of judicious
            # processing we want to do in `messy_ugly_analyze_node_state`.
            node_data['state_original_unprocessed'] = node_data['state']
            node_data['state'] = messy_ugly_analyze_node_state(node_data['state'])


            # Grafana wants UTC
            node_data['timestamp'] = utc_now

            # Boolean for state, only for Grafana colors.
            # TODO : See if this is actually being used in Grafana
            #        or if it was just a vestigial field in "sinfo.py".
            #        Get rid of it if possible, because it's happening at
            #        the wrong level of the pipeline.
            if node_data['state'] in self.slurm_node_states_color:
                node_data['grafana_helpers'] = {
                        'job_state_color': self.slurm_node_states_color[node_data['state']]
                }

            if node_data.get('reason_time', None) is not None:
                node_data['reason_time_str'] = datetime.fromtimestamp(node_data['reason_time']).astimezone().strftime('%Y-%m-%dT%H:%M:%S %Z')

            # Save in dict. Note that all the many (~18) possible node states are tallied.
            # This is not a projection down to 4 states like for the cpus/gpus.
            self.prom_node_states.labels(name=node_name).state(node_data['state'])


            ##############################################
            # CPUs

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


            ##############################################
            # GPUs

            # If the 'gres' field exists, and provided it's a list with at least one element.
            if node_data.get('gres', []):
                node_data['gpus'] = messy_ugly_analyze_gpu_gres(node_data['gres'], node_data['gres_used'])
                
                # Loop on sanitized gpus and set counters
                for gpu_name, gpu_counts in node_data['gpus'].items():
                    # gpu_name described the name of a product from nvidia (ex : "rtx8000", "m40", "k80")
                    # gpu_counts is a dict with keys ['total', 'alloc']

                    self.gpu_state_counters['total'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'])

                    # We need to test if the key is present because it isn't present when we use the not-pyslurm script on "cedar".
                    # This should be solved when we run pyslurm everywhere.
                    if 'alloc' in gpu_counts:
                        self.gpu_state_counters['alloc'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['alloc'])
                        # Test state: if node is available/mixed and a least 1 cpu is avail, gres are idle otherwise drain
                        # TODO : The comment from previous line was copied as it was in "sinfo.py".
                        #        We're not sure how good of an idea that was.
                        #        This is yet another of those situations where it's worth a discussion with the group.
                        if node_data['state'] not in NodeStatesManager.slurm_useless_node_states and node_data['idle_cpus']>1:
                            self.gpu_state_counters['idle'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'] - gpu_counts['alloc'])
                        else:
                            self.gpu_state_counters['drain'].labels(type=gpu_name, reservation=node_data["reservation"]).inc(gpu_counts['total'] - gpu_counts['alloc'])

            # Add Elastic Search action for each node.
            # We put the `es_nodes_body` construction here because
            # of the node_data['gpus'] that gets added in the above
            # code block.
            es_nodes_body.append({'index': {'_id': node_name}})
            es_nodes_body.append(node_data)

        # Send bulk update for Elastic Search
        if 'nodes_index' in self.D_elasticsearch_config and self.elasticsearch_client is not None:
            print(f"Want to bulk commit {len(es_nodes_body)//2} node_data values to ElasticSearch.")
            self.elasticsearch_client.bulk(
                index=self.D_elasticsearch_config['nodes_index'],
                body=es_nodes_body, timeout=self.D_elasticsearch_config['timeout'])

        if 'nodes_collection' in self.D_mongodb_config and self.mongo_client is not None:
            timestamp_start = time.time()
            L_updates_to_do = [
                UpdateOne(
                    # rule to match if already present in collection
                    {'name': node_data['name'], 'cluster_name': node_data['cluster_name']},
                    # the data that we write in the collection
                    {'$set': node_data},
                    # create if missing, update if present
                    upsert=True)
                for node_data in psl_nodes.values() ]
            # this is a one-liner, but we're breaking it into multiple steps to highlight the structure
            database = self.mongo_client[self.D_mongodb_config['database']]
            nodes_collection = database[self.D_mongodb_config['nodes_collection']]
            nodes_collection.bulk_write(L_updates_to_do) #  <- the actual work
            mongo_update_duration = time.time() - timestamp_start
            print(f"Bulk write for {len(L_updates_to_do)} node_data entries in mongodb took {mongo_update_duration} seconds.")


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
    job_date_fields = [ 'submit_time', 'start_time', 'end_time', 'eligible_time' ]


    def __init__(self,
        cluster_name:str, endpoint_prefix: str, D_cluster_desc: dict,
        D_elasticsearch_config:dict={}, elasticsearch_client:Elasticsearch=None,
        D_mongodb_config:dict={}, mongo_client=None):
    
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

        self.D_mongodb_config = D_mongodb_config
        self.mongo_client = mongo_client

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

            # print(f"type(job_id) : {type(job_id)}")
            # print(f'type(job_data["job_id"]) : {type(job_data["job_id"])}')
            # quit()

            # Some fields will be added to `job_state`
            # to make it more informative. These things
            # end up in ElasticSearch but they are not
            # found in the Prometheus metrics.

            # Infer the actual account of the person based on the job info.
            # See the documentation for more explanations about the three kinds
            # of usernames that we anticipate we'll have to manage.
            # 'cc_account_username', 'mila_cluster_username', 'mila_email_username'
            #
            if 'cc_account_username' in job_data and job_data['cc_account_username'] is not None:
                # This means that this was already supplied to us from the scraper.
                job_data['mila_cluster_username'] = "unknown"
                # job_data['cc_account_username'] already identified
                job_data['mila_email_username'] = "unknown"
            elif self.cluster_name == "mila":
                # We attempt to extract the username in the same way in both cases,
                # but we just place it at a different location.
                job_data['mila_cluster_username'] = extract_username_from_job_data(job_data)
                job_data['cc_account_username'] = "unknown"
                job_data['mila_email_username'] = "unknown"
            else:
                job_data['mila_cluster_username'] = "unknown"
                job_data['cc_account_username'] = extract_username_from_job_data(job_data)
                job_data['mila_email_username'] = "unknown"



            # Very useful for later when we untangle the sources in the plots.
            # Will also serve to have a unique id for entries in mongodb.
            job_data['cluster_name'] = self.cluster_name

            # Guillaume says : I'm unsure why Quentin does this.
            #if job_state not in self.slurm_job_states:
            #    self.slurm_job_states.append(job_state)
        
            # Quentin wrote that Grafana wanted UTC.
            job_data['timestamp'] = utc_now
            # Create display time for convenience.
            for key in self.job_date_fields:
                #        When those dates are not available, pyslurm writes `0` instead.
                #        This creates nonsensical dates when we convert them here into '%Y-%m-%dT%H:%M:%S %Z'.
                #        It's probably better to just have those be `None` instead.
                #
                #        Note that .astimezone() is always called on a computer that runs
                #        in the same timezone as Mila. When we remotely call the scraper
                #        on some cluster, we do it from a machine in the same timezone as Mila
                #        to this is where the timezone gets set. In any case, we add %Z to the
                #        strings so we could always recover from mistakes (and we store the original
                #        timestamps as well).
                if ((key in job_data) and
                    (job_data[key] is not None) and
                    (job_data[key] != 0)):
                    job_data[key + '_str'] = datetime.fromtimestamp(job_data[key]).astimezone().strftime('%Y-%m-%dT%H:%M:%S %Z')
                else:
                    job_data[key + '_str'] = None
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

            # Add ElasticSearch action for each job.
            # ES was setup for int(job_id) so we'll continue that,
            # but for mongodb we won't do that. Too much messing around
            # makes the code harder to predict. Pyslurm gives us text,
            # so we'll use text for the job_id in mongodb (not Elastic Search).
            #
            # One of the other difficulties here is that manual_flimsy_sinfo_scraper.py
            # is getting job_id values like "3114204_9", "3114204_9.extern", "3114204_9.batch"
            # or "5720367.interactive".
            # This is temporary, though, but we have to make a decision about it.
            # For now we'll skip the ".extern" and ".batch" from elasticsearch.
            # TODO : Decide if you should skip it entirely instead and not insert it in mongodb.
            #        In that case you could add this verification at the beginning
            #        of this parent `for (job_id, job_data) in ...`.
            if ".extern" in job_id or ".batch" in job_id:
                pass
            elif m:= re.match("^(\d+)\.interactive", job_id):
                es_jobs_body.append({'index': {'_id': int(m.group(1))}})
                es_jobs_body.append(job_data)
            elif m:= re.match("^(\d+)\.\d+", job_id):
                # e.g. '7943791.0'
                es_jobs_body.append({'index': {'_id': int(m.group(1))}})
                es_jobs_body.append(job_data)
            elif m:= re.match("^(\d+)_.*", job_id):
                # This was originally made to be (\d+)_\d+,
                # but one time we had job_id being "6380334_[0-11%4]",
                # so we updated the regex.
                es_jobs_body.append({'index': {'_id': int(m.group(1))}})
                es_jobs_body.append(job_data)
            else:
                # The normal thing that happens with data from legit pyslurm.
                es_jobs_body.append({'index': {'_id': int(job_id)}})
                # full body
                es_jobs_body.append(job_data)

        if 'jobs_index' in self.D_elasticsearch_config and self.elasticsearch_client is not None and es_jobs_body:
            print(f"Want to bulk commit {len(es_jobs_body) // 2} job_data values to ElasticSearch.")
            # Send bulk update for ElasticSearch.
            self.elasticsearch_client.bulk(
                index=self.D_elasticsearch_config['jobs_index'],
                body=es_jobs_body, timeout=self.D_elasticsearch_config['timeout'])
            # print("Done with commit to ElasticSearch.")

        if 'jobs_collection' in self.D_mongodb_config and self.mongo_client is not None and psl_jobs:
            timestamp_start = time.time()
            L_updates_to_do = [
                UpdateOne(
                    # Rule to match if already present in collection.
                    # Refrain from using keys job_id from psl_jobs because
                    # they might be str whereas the entries in the database are int.
                    # This is a source of headaches, but at least with this approach
                    # we'll get the upserts working properly.
                    {'job_id': job_data['job_id'], 'cluster_name': job_data['cluster_name']},
                    # the data that we write in the collection
                    {'$set': job_data},
                    # create if missing, update if present
                    upsert=True)
                    for job_data in psl_jobs.values() ]

            # this is a one-liner, but we're breaking it into multiple steps to highlight the structure
            database = self.mongo_client[self.D_mongodb_config['database']]
            jobs_collection = database[self.D_mongodb_config['jobs_collection']]
            result = jobs_collection.bulk_write(L_updates_to_do) #  <- the actual work
            # TODO : investigate why the updates aren't performed, and new entries are created instead
            # print(result.bulk_api_result)
            mongo_update_duration = time.time() - timestamp_start
            print(f"Bulk write for {len(L_updates_to_do)} job_data entries in mongodb took {mongo_update_duration} seconds.")