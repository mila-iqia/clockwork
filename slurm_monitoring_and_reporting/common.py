
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
