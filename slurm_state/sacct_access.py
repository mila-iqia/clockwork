

def fetch_data_with_sacct_on_remote_clusters(cluster_name, L_job_ids):
    """
    Fetches through SSH certain fields for jobs that have
    been dropped from scontrol_show_job prematurely before
    their final JobState was captured.
    Basically, we want to refrain from large queries
    to respect Compute Canada's wishes so we limit ourselves
    to one such query per job (in the entire lifecycle of the job)
    and we only retrieve fields that could have been updated
    during the life of the job (i.e. after it was first seen
    in scontrol_show_job).

    The intended use for this involves only jobs with a perceived
    `job_state` of "RUNNING" or "PENDING" in our MongoDB database.

    Returns a list of dict of the form
    {
        "job_id" : ...,
        "job_state" : ...,
        "start_time" : ...,
        "end_time" : ...,
        "submit_time" : ...,
        "exit_code" : ...
    }
    """
    return []