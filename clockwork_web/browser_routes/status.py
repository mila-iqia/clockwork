"""
Browser routes dealing with the "cluster" entity
"""
import logging

from flask import Blueprint, request
from flask_login import current_user, login_required
from flask_babel import gettext

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import get_jobs, get_filter_cluster_name
from clockwork_web.core.nodes_helper import get_nodes
from clockwork_web.core.users_helper import render_template_with_user_settings

flask_api = Blueprint("status", __name__)


@flask_api.route("/")
@login_required
def route_status():
    """Display status about clusters available for connected user."""
    logging.info(
        f"clockwork_web route: /clusters/status  - current_user={current_user.mila_email_username}"
    )

    # Get the clusters and reformat them in order to keep what we want.
    D_all_clusters = get_all_clusters()
    user_clusters = current_user.get_available_clusters()

    clusters = {}
    # Keep only clusters available for current user.
    for current_cluster_name in sorted(user_clusters):
        dct = {}

        # get job slurm updates.
        jobs, _ = get_jobs(cluster_names=[current_cluster_name])
        job_dates = [
            job["cw"]["last_slurm_update"]
            for job in jobs
            if "last_slurm_update" in job["cw"]
        ]
        # Get node slurm updates.
        nodes, _ = get_nodes(get_filter_cluster_name(current_cluster_name))
        node_dates = [
            node["cw"]["last_slurm_update"]
            for node in nodes
            if "last_slurm_update" in node["cw"]
        ]

        # Save min and max dates for jobs and nodes.
        if job_dates:
            dct["job_dates"] = {"min": min(job_dates), "max": max(job_dates)}
        if node_dates:
            dct["node_dates"] = {"min": min(node_dates), "max": max(node_dates)}

        clusters[current_cluster_name] = dct

    return render_template_with_user_settings(
        "status.html",
        all_clusters=clusters,
        mila_email_username=current_user.mila_email_username,
        previous_request_args={},
    )
