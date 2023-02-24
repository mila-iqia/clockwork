from types import SimpleNamespace

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import get_inferred_job_states
from clockwork_web.core.utils import (
    get_custom_array_from_request_args,
    normalize_username,
)


def parse_search_request(user, args, force_pagination=True):
    """Parse a search request.

    user: The current user.
    args: A reference to request.args.
    force_pagination: Whether to force pagination or not.
    """
    from clockwork_web.core.pagination_helper import get_pagination_values

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

    # Parse the list of states to filter for
    aggregated_states = get_custom_array_from_request_args(
        args.get("aggregated_job_state")
    )
    states = get_inferred_job_states(aggregated_states)
    states += get_custom_array_from_request_args(args.get("job_state"))

    query = SimpleNamespace(
        username=normalize_username(args.get("username")),
        cluster_name=cluster_names,
        aggregated_job_state=aggregated_states,
        job_state=states,
        pagination_page_num=args.get("page_num", type=int, default=default_page_number),
        pagination_nbr_items_per_page=args.get("nbr_items_per_page", type=int),
        sort_by=args.get("sort_by", default="submit_time", type=str),
        sort_asc=args.get("sort_asc", default=1, type=int),
    )

    #########################
    # Define the pagination #
    #########################

    if (
        force_pagination
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
