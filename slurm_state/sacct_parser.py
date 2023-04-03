import json

def ignore(k,v, res):
    pass

def copy(k,v,res):
    res[k]=v 

def rename(name):
    def renamer(k,v, res):
        res[name] = v
    return renamer

def rename_subitems(subitem_dict):
    def renamer(k,v,res):
        for subitem,name in subitem_dict.items():
            res[name] = v[subitem]
    return renamer

def join_subitems(separator,name):
    def joiner(k,v,res):
        values=[]
        for _,value in v.items():
            values.append(str(value))
        res[name] = separator.join(values)
    return joiner



# # This map should contain all the fields that come from parsing a job entry
# # Each field should be mapped to a handler that will process the string data
# # and set the result in the output dictionary.  You can ignore fields, by
# # assigning them to 'ignore'
JOB_FIELD_MAP = {
    "account": copy,
    "comment": ignore,
    "allocation_nodes": rename("num_nodes"),
    "array": ignore,
    "association": ignore,
    "cluster": ignore,
    "constraints": ignore,
    "derived_exit_code": ignore,
    "time": rename_subitems({
        "limit":"time_limit", 
        "submission":"submit_time", 
        "start":"start_time", 
        "end":"end_time", 
        }),
    "exit_code": join_subitems(":","exit_code"),
    "flags": ignore,
    "group": ignore,
    "het": ignore,
    "job_id": copy,
    "name": copy,
    "mcs": ignore,
    "nodes": copy,
    "partition": copy,
    "priority": ignore,
    "qos": ignore,
    "required": ignore,
    "kill_request_user": ignore,
    "reservation": ignore,
    "state": rename_subitems({"current":"job_state"}),
    "steps": ignore,
    "tres": ignore,
    "user": rename("username"),
    "wckey": ignore,
    "working_directory": ignore,

}

def job_parser(f):
    """
    This function parses a report of a sacct command (json format)
    that we can get with this kind of commands:

    /opt/software/slurm/bin/sacct -A rrg-bengioy-ad_gpu,rrg-bengioy-ad_cpu,def-bengioy_gpu,def-bengioy_cpu -X -S 2023-03-30T00:00 -E 2023-03-31T00:00 --json

    """
    sacct_data = json.load(f)
    # at this point, sacct_data is a hierarchical structure of dictionaries and lists

    src_jobs = sacct_data['jobs'] # jobs is a list 
    
    # example fields of a job:

    # account = rrg-cerise-ad_gpu
    # comment = {'administrator': None, 'job': None, 'system': None}
    # allocation_nodes = 1
    # array = {'job_id': 63692861, 'limits': {'max': {'running': {'tasks': 0}}}, 'task': None, 'task_id': 0}
    # association = {'account': 'rrg-cerise-ad_gpu', 'cluster': 'cedar', 'partition': None, 'user': 'nobody2'}
    # cluster = cedar
    # constraints = [p100|p100l|v100l]
    # derived_exit_code = {'status': 'SUCCESS', 'return_code': 0}
    # time = {'elapsed': 86307, 'eligible': 1680127992, 'end': 1680215981, 'start': 1680127992, 'submission': 1680127990, 'suspended': 0, 'system': {'seconds': 0, 'microseconds': 0}, 'limit': 1440, 'total': {'seconds': 0, 'microseconds': 0}, 'user': {'seconds': 0, 'microseconds': 0}}
    # exit_code = {'status': 'SUCCESS', 'return_code': 0}
    # flags = ['CLEAR_SCHEDULING', 'STARTED_ON_BACKFILL']
    # group = nobody2
    # het = {'job_id': 0, 'job_offset': None}
    # job_id = 63694682
    # name = submitit
    # mcs = {'label': ''}
    # nodes = cdr2529
    # partition = gpubase_bygpu_b3
    # priority = 1347301
    # qos = normal
    # required = {'CPUs': 4, 'memory': 40960}
    # kill_request_user = None
    # reservation = {'id': 0, 'name': 0}
    # state = {'current': 'REQUEUED', 'reason': 'Prolog'}
    # steps = []
    # tres = {'allocated': [{'type': 'cpu', 'name': None, 'id': 1, 'count': 4}, {'type': 'mem', 'name': None, 'id': 2, 'count': 40960}, {'type': 'node', 'name': None, 'id': 4, 'count': 1}, {'type': 'billing', 'name': None, 'id': 5, 'count': 1}, {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}], 'requested': [{'type': 'cpu', 'name': None, 'id': 1, 'count': 4}, {'type': 'mem', 'name': None, 'id': 2, 'count': 40960}, {'type': 'node', 'name': None, 'id': 4, 'count': 1}, {'type': 'billing', 'name': None, 'id': 5, 'count': 1}, {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}]}
    # user = nobody2
    # wckey = {'wckey': 'submitit', 'flags': []}
    # working_directory = /scratch/nobody2

    # wanted output format:

   # job_id "1234"
    # name "interactive"
    # username "nobody"
    # account "mila"
    # job_state "FAILED"
    # exit_code "1:0"
    # time_limit 43200
    # submit_time 1667708757
    # start_time 1678930026
    # end_time 1678930037
    # partition "main"
    # nodes "cn-d003"
    # num_nodes "1"
    # num_cpus "6"
    # num_tasks "1"
    # cpus_per_task "6"
    # TRES "cpu=6,mem=32G,node=1,billing=4,gres/gpu=2"
    # command null
    # work_dir "/home/mila/n/nobody"
    # tres_per_node "gres:gpu:a100:2"
    # cluster_name "mila"

    # We will use a handler mapping to translate this

    res_jobs=[]

    for src_job in src_jobs:
        res_job = dict()

        for k,v in src_job.items():
            translator = JOB_FIELD_MAP.get(k, None)
            if translator is None:
                raise ValueError(f"Unknown field in sacct job output: {k}")
            
            # translate
            translator(k,v, res_job)

        res_jobs.append(res_job)
        # yield res_job
    return res_jobs
