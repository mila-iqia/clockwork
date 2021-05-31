"""
This file contains a lot of the messy functions with hardcoded values or decisions in them.

extract_mila_user_account_from_job_data :
    Based on all the job_data, it's not clear who the actual user is.
    This is a bunch of rules to look at work_dir and other fields to
    make an educated guess based on the knowledge of the clusters.

filter_unrelated_jobs :
    Strip away every non-Mila related job from other clusters.
    This requires hardcoding the name "bengio".

messy_ugly_analyze_node_state:
    An undocumented and questionable function that reverse-engineers
    the node states listed by slurm.

messy_ugly_analyze_gpu_gres:
    An undocumented and questionable function that reverse-engineers
    the information on GPU allocation listed by slurm.

"""



from collections import defaultdict
import re


def extract_mila_user_account_from_job_data(job_data):
    """
    The exact user is not automatically included in the job_data.
    We need to infer it based on other fields.
    This involves a little bit of guesswork which is easy to do
    manually but can be automated by this function.

    TODO : Move this function away from this script.
    """

    potential_guesses = []

    def f(job_data, k):
        # avoid problems with entries that are present but are `None`
        return str(job_data.get(k, ""))
        

    ### mila cluster ###

    # "command": "/home/mila/d/dehganar/
    # "work_dir": "/home/mila/d/dehganar/scripts/camcan"
    # "std_err": "/home/mila/d/dehganar/randomsearch_906962.log",
    # "std_in": "/dev/null",
    # "std_out": "/home/mila/d/dehganar/randomsearch_906962.log",
    for k in ['command', 'std_err', 'std_in', 'std_out', 'work_dir']:
        if m := re.match(r"/home/mila/[a-zA-Z0-9]+/([^/]+?)/.*", f(job_data, k)):
            potential_guesses.append(m.group(1))

    ### beluga ###
    
    # "work_dir": "/scratch/prouse/log/WCSim_data_jobs/HyperK_2pi"
    # "std_err": "/scratch/prouse/log/WCSim_data_jobs/HyperK_2pi/gamma-750.err",
    # "std_in": "/dev/null",
    # "std_out": "/scratch/prouse/log/WCSim_data_jobs/HyperK_2pi/gamma-750.out",

    for k in ['std_err', 'std_in', 'std_out', 'work_dir']:
        if m := re.match(r"/scratch/([^/]+?)/.*", f(job_data, k)):
            potential_guesses.append(m.group(1))


    # "std_err": "/lustre03/project/6008004/yanlin/nextTadCaller/downsample/slurm-19741310.out",
    # "std_in": "/dev/null",
    # "std_out": "/lustre03/project/6008004/yanlin/nextTadCaller/downsample/slurm-19741310.out",
    # "work_dir": "/lustre03/project/6008004/yanlin/nextTadCaller/downsample",
    for k in ['std_err', 'std_in', 'std_out', 'work_dir']:
        if m := re.match(r"/lustre\d+/project/\d+/([^/]+?)/.*", f(job_data, k)):
            potential_guesses.append(m.group(1))

    # Be careful with this one because there are cases when the command
    # comes from /home/takaka-rrg

    # "command": "/home/pratogab/
    # "std_err": "/home/pratogab/ood_scaling_new/logs/proto_eval_coco_densenet121_data_ratio_100_percent_bird_5way_5shot.out",
    # "std_in": "/dev/null",
    # "std_out": "/home/pratogab/ood_scaling_new/logs/proto_eval_coco_densenet121_data_ratio_100_percent_bird_5way_5shot.out",
    # "work_dir": "/home/pratogab/ood_scaling_new",
    for k in ['command', 'std_err', 'std_in', 'std_out', 'work_dir']:
        if m := re.match(r"/home/([^/]+?)/.*", f(job_data, k)):
            potential_guesses.append(m.group(1))

    # "std_err": "/lustre04/scratch/fkaadou/Ag_Ca2N_MoS2/separate_layers/Ag_Ca2N/PES_scan/short_diag/scan11/slurm-19785495.out",
    # "std_in": "/dev/null",
    # "std_out": "/lustre04/scratch/fkaadou/Ag_Ca2N_MoS2/separate_layers/Ag_Ca2N/PES_scan/short_diag/scan11/slurm-19785495.out",
    for k in ['command', 'std_err', 'std_in', 'std_out', 'work_dir']:
        if m := re.match(r"/lustre\d+/scratch/\d+/([^/]+?)/.*", f(job_data, k)):
            potential_guesses.append(m.group(1))

    # Let's ignore that one because it's not even from us.
    # "account": "def-bhatnaga_cpu",
    # "std_err": "/home/gf591137/slurm-19828830.out",
    # "std_in": "/dev/null",
    # "std_out": "/home/gf591137/slurm-19828830.out",
    # "command": "/home/gf591137/projects/def-koualk/gf591137/typeI.sh",
    # "work_dir": "/home/gf591137",

    # Some of the rules might lead to the user being guessed at "mila",
    # which is wrong in all cases. For example, this can happen for
    #     'work_dir': '/home/mila/s/schwarzm/Github/transfer-ssl-rl'
    # and it's clearly not a good thing.
    # We will just remove those manually at this point.
    # Better to have "unknown" if nothing else could have been guessed
    # than to have "mila" pop up as user.
    potential_guesses = [e for e in potential_guesses if e != "mila"]

    # If we have a single guess, then declare it to be that.
    # Otherwise, vote.
    E = set(potential_guesses)
    if len(E) == 0:
        return "unknown"
    elif len(E) == 1:
        return potential_guesses[0]
    else:
        D = defaultdict(int)
        for guess in potential_guesses:
            D[guess] += 1

        # Vote.
        (max_guess, max_count) = sorted(D.items(), key=lambda e: e[1])[-1]
        return max_guess


def filter_unrelated_jobs(psl_jobs):
    """
    Remove non-bengio non-mila jobs.

    This is normally done on the collection side automatically
    to save on bandwidth. However, this gets skipped if we load
    the data from a file. It's supposed to be a lightweight operation
    so there's no harm filtering twice (especially since it's cheaper
    the second time around with a shorter list).
    """
    accounts = set(v['account'] for v in psl_jobs.values())
    valid_accounts = set(
        [a for a in accounts if re.match(r".*bengio.*", a)] + ["mila"]
    )
    return dict((k, v) for (k, v) in psl_jobs.items() if v['account'] in valid_accounts)




def messy_ugly_analyze_node_state(node_state:str):
    """
    Used exclusively by NodeStatesManager.
    Factored out because it's ugly and full of arbitrary
    decisions based on patterns not explicitly stated.

    This complicated mess comes from "sinfo.py" and we need to be
    able to factor it out in order to reason about it.
    
    This function seriously needs documentation, motivation,
    and unit tests. Otherwise it's unacceptable.

    This is about reverse-engineering the string from slurm.
    """

    # Split if node has 2 states
    if '+' in node_state:
        multi = False
        node_state = node_state.split("+")
        # Keep only 1 state DOWN>DRAIN>REST
        # UGLY: TODO better
        for _s in node_state:
            if _s.startswith('DOWN'):
                multi = "DOWN"
                break
            elif _s.startswith('DRAIN'):
                # DRAIN assumes DRAINED
                multi = "DRAINED"
        if not multi:
            multi = node_state[0]
        # Save
        node_state = multi

    # Count not responding nodes separatly
    if node_state.endswith('*'):
        node_state = node_state[:-1]
    # TODO: count reboots ?
    if node_state.endswith((('#', '@'))):
        node_state = node_state[:-1]

    node_state = node_state.lower()
    return node_state


def messy_ugly_analyze_gpu_gres(node_gres, node_gres_used):
    """
    You have something like the following, and you want to make it intelligible.

        "gres": [
            "gpu:rtx8000:8(S:0-1)"
        ],
        "gres_drain": "N/A",
        "gres_used": [
            "gpu:rtx8000:8(IDX:0-7)",
            "tpu:0"
        ],

    What do you do?

    This function takes the two specific fields as argument because
    we don't want to pass the whole `node_data` and obfuscate
    the fact that the analysis is done only with those two fields.

    It returns a dict of the form
    {
        "k80":  {"total": 4, "alloc":3},
        "m40":  {"total": 2, "alloc":2},
    }

    TODO :  This function was ripped from "sinfo.py" without much more analysis.
            It would be good to write unit tests and explain what the expectations are.
            This would be a distraction now because we can start by assuming that it
            does the job fine (it certainly used to do it fine with "sinfo.py")
            and later we can investigate if things aren't working.

            Hopefully the obvious name of this function should attract attention
            to it and signal the need to understand/document it better.
    """
    ##############################################
    # GPUs

    # Build this variable as the output of this function.
    node_gpus = {}
    # Loop on Gres
    for g_tot in node_gres:
        g_tot = g_tot.split(':',2)
        if len(g_tot) == 3:
            node_gpus.setdefault(g_tot[1], {})['total'] = int(g_tot[2].split('(')[0])
    # Loop on Gres used
    for g_used in node_gres_used:
        g_used = g_used.split(':',2)
        # Exclude MPS for now
        if len(g_used) == 3:
            # Remove IDX index
            node_gpus.setdefault(g_used[1], {})['alloc'] = int(g_used[2].split('(')[0])
        
    return node_gpus