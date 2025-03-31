import re
import time

import json
from flask import g
from flask import request, make_response
from flask.json import jsonify
from flask.globals import current_app

from clockwork_web.core.search_helper import search_request
from .authentication import authentication_required
from ..db import get_db
from ..user import User
import logging

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import (
    get_filter_after_end_time,
    get_filter_cluster_name,
    get_filter_job_id,
    combine_all_mongodb_filters,
    strip_artificial_fields_from_job,
    get_jobs,
)
from clockwork_web.core.utils import to_boolean, get_custom_array_from_request_args
from clockwork_web.core.job_user_props_helper import (
    get_user_props,
    set_user_props,
    delete_user_props,
    HugeUserPropsError,
)

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

    logging.info(
        f"clockwork REST route: /jobs/list - current_user_with_rest_auth={current_user_id}"
    )

    # want_count = request.args.get("want_count", type=str, default="False")
    # want_count = to_boolean(want_count)

    # Parse the request arguments
    (query, LD_jobs, nbr_total_jobs) = search_request(
        current_user,
        request.args,
        force_pagination=False,
    )

    # Return the requested jobs, and the number of all the jobs
    LD_jobs = [
        strip_artificial_fields_from_job(D_job) for D_job in LD_jobs
    ]  # Remove the field "_id" of each job before jsonification
    if query.want_count:
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

    logging.info(
        f"clockwork REST route: /jobs/one - current_user_with_rest_auth={current_user_id}"
    )

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

    # If the current user is not an admin, we only retrieve his/her jobs
    username = None
    if not current_user.is_admin():
        username = current_user.mila_email_username

    # Set up the filters and retrieve the expected job
    (LD_jobs, _) = get_jobs(
        username=username, job_ids=[job_id], cluster_names=cluster_names
    )

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

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    return jsonify(D_job)


@flask_api.route("/jobs/user_props/get")
@authentication_required
def route_user_props_get():
    """
    Endpoint to get user props.

    Parameters: job_id (str), cluster_name (str)

    Return: user props
    """
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    logging.info(
        f"clockwork REST route: /jobs/user_props/get - current_user_with_rest_auth={current_user_id}"
    )

    # Retrieve the requested job ID
    job_id = request.values.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request

    # Retrieve the requested cluster name
    cluster_name = request.values.get("cluster_name", None)
    if cluster_name is None:
        return jsonify("Missing argument cluster_name."), 400  # bad request

    # Get props, using current_user_id as mila email username.
    props = get_user_props(job_id, cluster_name, current_user_id)
    return jsonify(props)


@flask_api.route("/jobs/user_props/set", methods=["PUT"])
@authentication_required
def route_user_props_set():
    """
    Endpoint to set user props

    Parameters: job_id (str), cluster_name (str), updates (dict)

    Return: updated user props
    """
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    logging.info(
        f"clockwork REST route: /jobs/user_props/set - current_user_with_rest_auth={current_user_id}"
    )

    if not request.is_json:
        return jsonify("Expected a JSON request"), 400  # bad request

    params = request.get_json()

    # Retrieve the requested job ID
    job_id = params.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request

    # Retrieve the requested cluster name
    cluster_name = params.get("cluster_name", None)
    if cluster_name is None:
        return jsonify("Missing argument cluster_name."), 400  # bad request

    # Retrieve the requested updates.
    updates = params.get("updates", None)
    if updates is None:
        return jsonify(f"Missing argument 'updates'."), 500
    if not isinstance(updates, dict):
        return (
            jsonify(
                f"Expected `updates` to be a dict, but instead it is of type {type(updates)}: {updates}."
            ),
            500,
        )

    # Set props, using current_user_id as mila email username.
    try:
        props = set_user_props(job_id, cluster_name, updates, current_user_id)
        return jsonify(props)
    except HugeUserPropsError as inst:
        # If props size limit error occurs, return it as an HTTP 500 error.
        return jsonify(str(inst)), 500
    except:
        return jsonify("Failed to set user props."), 500


@flask_api.route("/jobs/user_props/delete", methods=["PUT"])
@authentication_required
def route_user_props_delete():
    """
    Endpoint to delete user props.

    Parameters: job_id (str), cluster_name (str), keys (string or list of strings)

    Return: updated user props
    """
    current_user_id = g.current_user_with_rest_auth["mila_email_username"]
    logging.info(
        f"clockwork REST route: /jobs/user_props/delete - current_user_with_rest_auth={current_user_id}"
    )

    if not request.is_json:
        return jsonify("Expected a JSON request"), 400  # bad request

    params = request.get_json()

    # Retrieve the requested job ID
    job_id = params.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request

    # Retrieve the requested cluster name
    cluster_name = params.get("cluster_name", None)
    if cluster_name is None:
        return jsonify("Missing argument cluster_name."), 400  # bad request

    # Retrieve the requested keys.
    keys = params.get("keys", None)
    if keys is None:
        return jsonify(f"Missing argument 'keys'."), 500
    if not isinstance(keys, (str, list)):
        return (
            jsonify(
                f"Expected `keys` to be a string or list of strings, instead it is of type {type(keys)}: {keys}."
            ),
            500,
        )

    # Delete props, using current_user_id as mila email username.
    delete_user_props(job_id, cluster_name, keys, current_user_id)
    return jsonify("")
