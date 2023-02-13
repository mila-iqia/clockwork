import re
import time

import json
from flask import g
from flask import request, make_response
from flask.json import jsonify
from flask.globals import current_app
from .authentication import authentication_required
from ..db import get_db
from ..user import User

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import (
    get_filter_after_end_time,
    get_filter_cluster_name,
    get_filter_job_id,
    combine_all_mongodb_filters,
    strip_artificial_fields_from_job,
    get_jobs,
    infer_best_guess_for_username,
)
from clockwork_web.core.utils import to_boolean, get_custom_array_from_request_args

from flask import Blueprint

flask_api = Blueprint("rest_jobs", __name__)


@flask_api.route("/jobs/list")
@authentication_required
def route_api_v1_jobs_list():
    """

    .. :quickref: list all Slurm jobs
    """
    # Retrieve the authentified user
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    current_user = User.get(current_user_id)

    # Retrieve the parameters used to filter the jobs
    # - username: ID of the user who launched the jobs we are looking for
    username = request.args.get("username", None)
    want_count = request.args.get("want_count", type=str, default="False")

    want_count = to_boolean(want_count)

    # - clusters
    requested_cluster_names = get_custom_array_from_request_args(
        request.args.get("cluster_name")
    )
    if len(requested_cluster_names) < 1:
        # If no cluster has been requested, then all clusters have been requested
        # (a filter related to which clusters are available to the current user
        #  is then applied)
        requested_cluster_names = get_all_clusters()

    # Limit the cluster options to the clusters the user can access
    user_clusters = (
        current_user.get_available_clusters()
    )  # Retrieve the clusters the user can access
    cluster_names = [
        cluster for cluster in requested_cluster_names if cluster in user_clusters
    ]

    # If cluster_names is empty, then the user does not have access to any cluster (s)he
    # requested. Thus, an empty jobs list is returned
    if len(cluster_names) < 1:
        if want_count:
            return jsonify({"nbr_total_jobs": 0, "jobs": []})
        else:
            return jsonify([])

    # - states: the possible states of the jobs we are looking for
    states = get_custom_array_from_request_args(request.args.get("state"))

    # Pagination values
    pagination_page_num = request.args.get("page_num", type=int)
    pagination_nbr_items_per_page = request.args.get("nbr_items_per_page", type=int)

    # Set up the pagination parameters
    if not pagination_page_num and not pagination_nbr_items_per_page:
        # In this particular case, we set the default pagination arguments to be `None`,
        # which will effectively disable pagination.
        nbr_skipped_items = None
        nbr_items_to_display = None
    else:
        # Otherwise (ie if at least one of the pagination parameters is provided),
        # we assume that a pagination is expected from the user. Then, the pagination helper
        # is used to define the number of elements to skip, and the number of elements to display
        (nbr_skipped_items, nbr_items_to_display) = get_pagination_values(
            current_user.mila_email_username,
            pagination_page_num,
            pagination_nbr_items_per_page,
        )

    # Call a helper to retrieve the jobs
    (LD_jobs, nbr_total_jobs) = get_jobs(
        username=username,
        cluster_names=cluster_names,
        states=states,
        nbr_skipped_items=nbr_skipped_items,
        nbr_items_to_display=nbr_items_to_display,
        want_count=want_count,
    )

    # Return the requested jobs, and the number of all the jobs
    LD_jobs = [
        strip_artificial_fields_from_job(D_job) for D_job in LD_jobs
    ]  # Remove the field "_id" of each job before jsonification
    if want_count:
        return jsonify({"nbr_total_jobs": nbr_total_jobs, "jobs": LD_jobs})
    else:
        return jsonify(LD_jobs)


@flask_api.route("/jobs/one")
@authentication_required
def route_api_v1_jobs_one():
    """

    .. :quickref: list one Slurm job
    """
    # Retrieve the authentified user
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    current_user = User.get(current_user_id)

    # Retrieve the requested job ID
    job_id = request.values.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request

    # Retrieve the requested cluster names
    requested_cluster_names = get_custom_array_from_request_args(
        request.args.get("cluster_name")
    )
    if len(requested_cluster_names) < 1:
        # If no cluster has been requested, then all clusters have been requested
        # (a filter related to which clusters are available to the current user
        #  is then applied)
        requested_cluster_names = get_all_clusters()
    # Limit the cluster options to the clusters the user can access
    user_clusters = (
        current_user.get_available_clusters()  # Retrieve the clusters the user can access
    )
    cluster_names = [
        cluster for cluster in requested_cluster_names if cluster in user_clusters
    ]

    # If cluster_names is empty, then the user does not have access to any
    # of the clusters they requested. Thus, an empty job dictionary is returned
    if len(cluster_names) < 1:
        return jsonify({}), 200

    # Set up the filters and retrieve the expected job
    (LD_jobs, _) = get_jobs(job_ids=[job_id], cluster_names=cluster_names)

    if len(LD_jobs) == 0:
        # Not a great when missing the value we want, but it's an acceptable answer.
        return jsonify({}), 200
    if len(LD_jobs) > 1:
        # This can actually happen if two clusters use the same id
        # Perhaps the rest API should always return a list?
        resp = (
            jsonify(
                f"Found {len(LD_jobs)} jobs with job_id {job_id}. Not sure what to do about these cases."
            ),
            500,
        )

    # TODO : Potential redesign. See CW-81.
    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)

    return jsonify(D_job)


# Note that this whole `user_dict_update` thing needs to be rewritten
# in order to use Olivier's proposal about jobs properties
# being visible only to the users that set them,
# and where everyone can set properties on all jobs.


@flask_api.route("/jobs/user_dict_update", methods=["PUT"])
@authentication_required
def route_api_v1_jobs_user_dict_update():
    """
        Performs an update to the user dict for a given job.
        The request needs to contain "job_id" and "cluster_name"
        to identify the job to be updated, and then it needs to contain
        "update_pairs" which is a list of (k, v), as a json string,
        that we should update in the `job["user"]` dict.
        The reason for passing "update_pairs" as a string is that
        Flask received it as `werkzeug.datastructures.FileStorage`
        when it was sent as a dict instead of a string.

        User info is in `g.current_user_with_rest_auth`.

        Returns the updated user dict.

    .. :quickref: update the user dict for a given Slurm job that belongs to the user
    """
    # Retrieve the authentified user
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    current_user = User.get(current_user_id)

    # A 'PUT' method is generally to modify resources.
    # Retrieve the provided job ID
    job_id = request.values.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request

    # Retrieve the provided cluster names
    requested_cluster_names = get_custom_array_from_request_args(
        request.args.get("cluster_name")
    )
    if len(requested_cluster_names) < 1:
        # If no cluster has been requested, then all clusters have been requested
        # (a filter related to which clusters are available to the current user
        #  is then applied)
        requested_cluster_names = get_all_clusters()

    # Limit the cluster options to the clusters the user can access
    user_clusters = (
        current_user.get_available_clusters()
    )  # Retrieve the clusters the user can access
    cluster_names = [
        cluster for cluster in requested_cluster_names if cluster in user_clusters
    ]

    # If cluster_names is empty, then the user does not have access to any cluster (s)he
    # requested. Thus, an error is returned
    if len(cluster_names) < 1:
        return (
            jsonify("It seems you have no access to the requested cluster(s)."),
            403,
        )

    # Note that we'll have to add some more fields when we make progress in CW-93.
    # We are going to have to check for "array_job_id" and "array_task_id"
    # if those are supplied to identify jobs in situations where the "job_id"
    # are "cluster_name" are insufficient.
    (LD_jobs, _) = get_jobs(job_ids=[job_id], cluster_names=cluster_names)
    # Note that `filter` gets reused later to commit again to the database.

    if len(LD_jobs) == 0:
        # Note that, if we wanted to have "phantom entries" in some other collection,
        # before the the jobs are present in the database, then we would need to adjust
        # this code branch to allow for updates even when no such jobs are currently found.
        return jsonify("Job not found in database."), 404
    if len(LD_jobs) > 1:
        resp = (
            jsonify(
                f"Found more than one job matching the criteria. This is probably not what was intended."
            ),
            500,
        )
        return resp

    D_job = LD_jobs[0]

    assert (
        hasattr(g, "current_user_with_rest_auth")
        and g.current_user_with_rest_auth is not None
    ), "Authentication should have failed much earlier than this."

    # Make use of `current_user_with_rest_auth`.
    # If the user requesting the update is not the owner,
    # then we refuse the update and return an error
    # that describes the problem.

    for key in ["mila_email_username", "mila_cluster_username", "cc_account_username"]:
        # Be as strict as possible here. If the job entry
        # contains any of the three types of usernames (and it's not `None`),
        # than it must be matched against that of the user
        # authenticated and submitting the request to modify
        # the user_dict. Usernames that are `None` but disagree
        # with each other will not cause failed matches.
        if D_job["cw"].get(key, None):
            if D_job["cw"][key] != g.current_user_with_rest_auth[key]:
                return (
                    jsonify(
                        f'This job belongs to {D_job["cw"][key]} and not {g.current_user_with_rest_auth[key]}.'
                    ),
                    403,  ## response code for "authorization denied"
                )

    update_pairs = request.values.get("update_pairs", None)
    if isinstance(update_pairs, dict):
        # This won't happen, but it would be nice if that were possible
        # instead of getting a `FileStorage` in Flask.
        pass
    elif update_pairs is None:
        return jsonify(f"Missing 'update_pairs' from arguments."), 500
    elif isinstance(update_pairs, str):
        try:
            update_pairs = json.loads(update_pairs)
        except Exception as inst:
            return jsonify(f"Failed to json.loads(update_pairs). \n{inst}."), 500
    else:
        return (
            jsonify(
                f"Field 'update_pairs' was not a string (encoding a json structure). {update_pairs}"
            ),
            500,
        )

    new_user_dict = D_job["user"] | update_pairs
    # We do an update with the database if we have an empty list
    # for `update_pairs`, for the sake of more predictable behavior.

    # We could reuse `filter` because we might as well refer to the job
    # by its "_id" instead since we have it. Maybe this can mitigate the
    # unlikely risk of `filter`` returning more matches than a moment ago
    # because updates were made in-between.
    # In any case, with the current setup we are still exposed to the
    # possibility that rapid updates to the same job could compete with
    # each other (and that's kinda fine).
    mc = get_db()
    result = mc["jobs"].update_one(
        {"_id": D_job["_id"]}, {"$set": {"user": new_user_dict}}, upsert=False
    )

    # See "https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html"
    # for the properties of the returned object.
    if result.modified_count == 1:
        return jsonify(new_user_dict), 200
    else:
        # Will that return a useful string as an error?
        return jsonify(f"Problem during update of the user dict. {result}"), 500
