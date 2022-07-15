"""
Browser routes dealing with the "cluster" entity
"""

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from clockwork_web.core.clusters_helper import get_all_clusters

flask_api = Blueprint("clusters", __name__)


@flask_api.route("/one")
@login_required
def route_one():
    """
    Display a HTML page presenting a cluster.

    Takes cluster_name as argument. It could be any name in ["beluga", "cedar", "graham", "mila", "narval"]

    Returns:
        200 (Success) and a dictionary describing the requested cluster
        400 (Bad Request) if the argument cluster_name is missing
        404 (Not Found) if the cluster_name is not in our list of known clusters


    .. :quickref: present a cluster as formatted HTML
    """
    # Retrieve the argument cluster_name
    cluster_name = request.args.get("cluster_name", None)

    # Get the clusters and reformat them in order to keep what we want
    # We make a copy in order to avoid unwillingly modify the original dictionary
    D_all_clusters = get_all_clusters()
    D_clusters = {}

    for current_cluster_name in D_all_clusters:
        copy = D_all_clusters[current_cluster_name].copy()
        del copy["allocations"]
        copy["timezone"] = str(copy["timezone"])
        D_clusters[current_cluster_name] = copy

    # Check if cluster_name is contained in the expected cluster names
    if cluster_name:
        if cluster_name in D_clusters:
            # Return a HTML page presenting the requested cluster's information
            return render_template(
                "cluster.html",
                cluster_name=cluster_name,
                cluster=D_clusters[cluster_name],
                mila_email_username=current_user.mila_email_username,
            )
        else:
            # Return a 404 error (Not Found) if the cluster is unknown
            return (
                render_template(
                    "error.html", error_msg=gettext("This cluster is not known.")
                ),
                404,  # Not Found
            )

    else:
        # Return a 400 error (Bad Request) if no cluster_name has been provided
        return (
            render_template(
                "error.html", error_msg=gettext("The argument cluster_name is missing.")
            ),
            400,  # Bad Request
        )
