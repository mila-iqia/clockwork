from datetime import datetime, timedelta

from clockwork_web.config import register_config
from clockwork_web.core.clusters_helper import get_all_clusters
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config


def main():
    # Register the elements to access the database
    register_config("mongo.connection_string", "")
    register_config("mongo.database_name", "clockwork")

    # Get database and collection objects
    client = get_mongo_client()
    db_insertion_point = client[get_config("mongo.database_name")]
    collection_name = "cluster_status"
    collection = db_insertion_point[collection_name]

    # Get clusters
    clusters = get_all_clusters()

    # Generate clusters statuses
    cluster_to_status = []
    for cluster_name in clusters:
        # Cluster error cannot yet be checked, so
        # cluster_has_error is always False for now.
        cluster_has_error = False
        cluster_to_status.append(
            {
                "cluster_name": cluster_name,
                "jobs_are_old": _jobs_are_old(db_insertion_point, cluster_name),
                "cluster_has_error": cluster_has_error,
            }
        )

    # Create collection index if necessary
    if not list(collection.list_indexes()):
        print("Create index for collection:", collection_name)
        collection.create_index(
            [
                ("cluster_name", 1),
                ("jobs_are_old", 1),
                ("cluster_has_error", 1),
            ],
            name="cluster_status_index",
        )
    # Save clusters statuses in database
    for cluster_status in cluster_to_status:
        collection.update_one(
            {"cluster_name": cluster_status["cluster_name"]},
            {"$set": cluster_status},
            upsert=True,
        )

    print("Updated.")


def _jobs_are_old(mc, cluster_name):
    """Return True if last slurm update in given cluster is older than 2 days."""
    jobs_are_old = False

    mongodb_filter = {"slurm.cluster_name": cluster_name}
    job_with_max_cw_last_slurm_update = list(
        mc["jobs"].find(mongodb_filter).sort([("cw.last_slurm_update", -1)]).limit(1)
    )

    if job_with_max_cw_last_slurm_update:
        (job,) = job_with_max_cw_last_slurm_update
        if "last_slurm_update" in job["cw"]:
            most_recent_job_edition = job["cw"]["last_slurm_update"]
            current_timestamp = datetime.now().timestamp()
            elapsed_time = timedelta(
                seconds=current_timestamp - most_recent_job_edition
            )
            # Let's say the latest jobs edition must not be older than max_delay.
            max_delay = timedelta(days=2)
            jobs_are_old = elapsed_time > max_delay

    return jobs_are_old


if __name__ == "__main__":
    main()
