"""
Browser routes dealing with the "cluster" entity
"""
import logging

from flask import Blueprint, request
from flask_login import current_user, login_required
from flask_babel import gettext

from clockwork_web.core.clusters_helper import get_all_clusters
from clockwork_web.core.jobs_helper import get_jobs
from clockwork_web.core.users_helper import (
    render_template_with_user_settings,
    get_users,
)

flask_api = Blueprint("status", __name__)


@flask_api.route("/")
@login_required
def route_status():
    """Display status about clusters available for connected user."""
    logging.info(
        f"clockwork_web route: /clusters/status  - current_user={current_user.mila_email_username}"
    )

    users = get_users()

    # Count users.
    nb_users = len(users)

    # Count enabled users.
    nb_enabled_users = sum(
        (1 for user in users if user["status"] == "enabled"), start=0
    )

    # Count users that have a DRAC account.
    # User has a DRAC account if user dict contains a valid value for field "cc_account_username".
    nb_drac_users = sum(
        (1 for user in users if user.get("cc_account_username", None)), start=0
    )

    # Collect clusters status:
    # - Count number of jobs per cluster.
    # - Get oldest and latest job modification dates in each cluster.
    D_all_clusters = get_all_clusters()
    clusters = {}
    for current_cluster_name in D_all_clusters:
        jobs, _ = get_jobs(cluster_names=[current_cluster_name])
        job_dates = [
            job["cw"]["last_slurm_update"]
            for job in jobs
            if "last_slurm_update" in job["cw"]
        ]
        clusters[current_cluster_name] = {
            "display_order": D_all_clusters[current_cluster_name]["display_order"],
            "nb_jobs": len(jobs),
        }
        if job_dates:
            clusters[current_cluster_name]["job_dates"] = {
                "min": min(job_dates),
                "max": max(job_dates),
            }

    server_status = {
        "nb_users": nb_users,
        "nb_enabled_users": nb_enabled_users,
        "nb_drac_users": nb_drac_users,
        "clusters": clusters or None,
    }

    return render_template_with_user_settings(
        "status.html",
        server_status=server_status,
        mila_email_username=current_user.mila_email_username,
        previous_request_args={},
    )
