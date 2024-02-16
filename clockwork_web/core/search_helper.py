from types import SimpleNamespace

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import get_inferred_job_states, get_jobs
from clockwork_web.core.utils import (
    get_custom_array_from_request_args,
    to_boolean,
)


def parse_search_request(user, args, force_pagination=True):
    """Parse a search request.

    user: The current user.
    args: A reference to request.args.
    force_pagination: Whether to force pagination or not.
    """
    from clockwork_web.core.pagination_helper import get_pagination_values

    want_count = args.get("want_count", type=str, default="False")
    want_count = to_boolean(want_count)

    job_array = args.get("job_array", type=int, default=None)
    job_label_name = args.get("job_label_name", type=str, default=None) or None
    job_label_content = args.get("job_label_content", type=str, default=None) or None

    default_page_number = "1" if force_pagination else None

    # Parse the list of clusters
    requested_cluster_names = get_custom_array_from_request_args(
        args.get("cluster_name")
    )
    if len(requested_cluster_names) < 1:
        # If no cluster has been requested, then all clusters have been requested
        # (a filter related to which clusters are available to the current user
        #  is then applied)
        requested_cluster_names = list(get_all_clusters().keys())
    user_clusters = (
        user.get_available_clusters()  # Retrieve the clusters the user can access
    )
    cluster_names = [
        cluster for cluster in requested_cluster_names if cluster in user_clusters
    ]

    # Parse the list of job states to filter for
    aggregated_job_states = get_custom_array_from_request_args(
        args.get("aggregated_job_state")
    )
    job_states = get_inferred_job_states(aggregated_job_states)
    job_states += get_custom_array_from_request_args(args.get("job_state"))

    job_ids = get_custom_array_from_request_args(args.get("job_id"))
    # Set default value of sort_asc
    sort_by = args.get("sort_by", default="submit_time", type=str)
    sort_asc = args.get("sort_asc", default=0, type=int)
    if sort_asc not in (-1, 1):
        if sort_by in ["cluster_name", "user", "name", "job_state"]:
            # Default value of sort_asc is ascending in these cases
            sort_asc = 1
        else:
            # Default value of sort_asc is descending otherwise
            sort_asc = -1

    query = SimpleNamespace(
        username=args.get("username"),
        cluster_name=cluster_names,
        aggregated_job_state=aggregated_job_states,
        job_state=job_states,
        job_ids=job_ids,
        pagination_page_num=args.get("page_num", type=int, default=default_page_number),
        pagination_nbr_items_per_page=args.get("nbr_items_per_page", type=int),
        sort_by=sort_by,
        sort_asc=sort_asc,
        want_count=want_count,
        job_array=job_array,
        job_label_name=job_label_name,
        job_label_content=job_label_content,
    )

    #########################
    # Define the pagination #
    #########################

    if (
        not force_pagination
        and not query.pagination_page_num
        and not query.pagination_nbr_items_per_page
    ):
        # In this particular case, we set the default pagination arguments to be `None`,
        # which will effectively disable pagination.
        query.nbr_skipped_items = None
        query.nbr_items_to_display = None
    else:
        # Otherwise (ie if at least one of the pagination parameters is provided),
        # we assume that a pagination is expected from the user. Then, the pagination helper
        # is used to define the number of elements to skip, and the number of elements to display
        (query.nbr_skipped_items, query.nbr_items_to_display) = get_pagination_values(
            user.mila_email_username,
            query.pagination_page_num,
            query.pagination_nbr_items_per_page,
        )

    return query


def search_request(user, args, force_pagination=True):
    query = parse_search_request(user, args, force_pagination=force_pagination)

    # Call a helper to retrieve the jobs
    (jobs, nbr_total_jobs) = get_jobs(
        username=query.username,
        cluster_names=query.cluster_name,
        job_states=query.job_state,
        job_ids=query.job_ids,
        nbr_skipped_items=query.nbr_skipped_items,
        nbr_items_to_display=query.nbr_items_to_display,
        want_count=force_pagination
        or query.want_count,  # The count is needed if there is pagination or if it is requested
        sort_by=query.sort_by,
        sort_asc=query.sort_asc,
        job_array=query.job_array,
        job_label_name=query.job_label_name,
        job_label_content=query.job_label_content,
    )
    return (query, jobs, nbr_total_jobs)
