# slurm_monitoring_and_reporting
Simple metrics to monitor slurm and produce reports.


## thoughts from adapting Quentin's code

### an opportunity to revisit decisions

Some decisions such as the representation for timestamps were made
in the original "sinfo.py" script. We can either implement exactly
the same interface, or we can improve in some places.
Improvements should be discussed with the team in general
to avoid being just arbitrary modifications, and the downside
is that certain historical graphs in Prometheus are going to be lost.

If we change the name of quantities, then the plots using those
quantities are no longer to be valid. This was probably not
the main goal for using Prometheus in the first place anyways,
so it should be fair game.

### elastic search is not being used for it's main feature : searching text

Elastic Search is being used a key-value database where updates
are performed based on `job_id`. Jobs in there will eventually
gravitate towards a terminal state and they will stay like that
in the database without any consideration about what happened in
their lifetime.

Moreover, we are not going to research their bodies for keywords,
which makes Elastic Search simply a glorified key-value database,
and possibly an overly complicated one at that.
Mongodb would offer nice opportunities to use Python to manipulate
its contents, unlike Elastic Search.

### reservation() is used only for nodes, not jobs

We don't need a ReservationManager and a NodeManager.
Everything from `pyslurm.reservation().get()` is used only for `pyslurm.node().get()`.

## follow up on these things

### slurm_job_states_color and slurm_node_states_color

If nobody is using job_data['job_state_code'] in Grafana, then we should probably get rid of it.
We included it for backward compatibility, but it's not a clean design in any case.

### job_id not being unique across clusters

There is a problem due to the fact that we are indexing jobs in ElasticSearch with job_id
and they are not unique across clusters. This is probably fine on most days,
but it will create issues if there is ever an overlap between two clusters.

We could avoid this by using a different Elastic Search index in the database, but then this
feels like possibly a premature split of clusters. It goes against the idea
of having multiple clusters all play with the same pool of jobs.

We could modify the "_id" to integrate the cluster name as well.
That's mostly a concern for Elastic Search and it's not anything fundamental.
Prometheus will address this by using a label to identify the cluster
when plotting graphs.

### collapse of states into just 4 states

In the `NodeStatesManager`, we are seriously collapsing the CPU states unto 4 values.
This might make the reporting easier, but anything problematic is turned into "drain".
```
if node_data['state'] not in NodeStatesManager.slurm_useless_states:
    self.cpu_state_counters['idle'].labels(reservation=node_data["reservation"]).inc(node_data['idle_cpus'])
else:
    # TODO : Whoa! This is NOT a node being drained. It could be in any number of problematic states.
    #        We're just not keeping track of the problematics states.
    self.cpu_state_counters['drain'].labels(reservation=node_data["reservation"]).inc(node_data['idle_cpus'])
```

The state "drain" is being used for every kind of error under the sun, and any state that's not usable right now (like "reboot").

For example, how are we supposed to this?
```
    "cn-a006": {
        "cpus": 80,
        "gres": [
            "gpu:rtx8000:8(S:0-1)"
        ],
        "gres_drain": "N/A",
        "gres_used": [
            "gpu:rtx8000:8(IDX:0-7)",
            "tpu:0"
        ],
        "name": "cn-a006",
        "alloc_cpus": 32,
        "err_cpus": 0,
        "state": "MIXED",
        ...
    },
```

## slurm_gpu_type not being used

Quentin's code has this:
```
    slurm_gpu_type=[]
```
and later
```
    for gpu in node['gpus']:
        # Add to static
        if gpu not in slurm_gpu_type:
            slurm_gpu_type.append(gpu)
```
However, this is never exposed in any way to Prometheus or Elastic Search.

I'm writing this thing here just as a note. It seems to me that this could have
been a kind of counter that he might have wanted to keep around but never
wrote it.

## Reclassification for state of GPUs.

I have no idea how justified this decision is. I just copied over the comment, but it's worth
thinking about it some more.

"# Test state: if node is available/mixed and a least 1 cpu is avail, gres are idle otherwise drain"

## nice profiling

When documenting this tool, it would be nice to have a nice profiling view.

## web interface

For the web interface, let's have a version that's not heavy javascript.
We can have the nice javascript-enhanced page, but also the plain one.

## total allocation on Compute Canada

It would be a good idea to have some kind of threshold shown in plots
that indicates the total gpu*years allocation that we have on certain clusters.
That would give us a certain idea of what to expect. Despite the fact
that the total number of gpus is listed, this isn't really the total
that we should expect to be using year round.

Those values could be pull from an endpoint that just serves constants.
The number of students could also be added to that endpoint.

