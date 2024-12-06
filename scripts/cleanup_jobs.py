"""
Script to clean-up jobs in database.

To evaluate job status, we check job["slurm"]["slurm_last_update"].
"""

import argparse
import sys
from datetime import datetime, timedelta
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config


def main(arguments: list):
    parser = argparse.ArgumentParser(description="Delete old jobs from database.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-n",
        "--jobs",
        type=int,
        help=(
            "Number of most recent jobs to keep. If specified, script will delete all older jobs until N jobs remain. "
            "If there were initially at most N jobs in database, nothing will be deleted."
        ),
    )
    group.add_argument(
        "-u",
        "--jobs-per-user",
        type=int,
        help=(
            "Number of most recent jobs to keep **PER USER**. "
            "If specified, script will delete all older jobs until N Jobss remain for each user. "
            "If a user initially had at most N jobs, all its jobs will remain."
        ),
    )
    group.add_argument(
        "-d",
        "--date",
        help=(
            "Date of older job to keep. "
            "Format 'YYYY-MM-DD-HH:MM:SS', or 'YYYY-MM-DD' (equivalent to 'YYYY-MM-DD-00:00:00'). "
            "If specified, script will delete all jobs older than given date."
        ),
    )
    group.add_argument(
        "-t",
        "--days",
        type=int,
        help=(
            "Time (in days) of older job to keep. "
            "If specified, script will delete all jobs updated before latest <--days> days."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "If specified, print info (job ID and slurm_last_update) "
            "about all available jobs before and after cleanup."
        ),
    )
    args = parser.parse_args(arguments)

    if args.debug:
        _debug_db_jobs()

    if args.jobs is not None:
        keep_n_most_recent_jobs(args.jobs)
    elif args.jobs_per_user is not None:
        keep_n_most_recent_jobs_per_user(args.jobs_per_user)
    elif args.days is not None:
        print(f"Keeping jobs updated in latest {args.days} days.")
        older_date = datetime.now() - timedelta(days=args.days)
        keep_jobs_from_date(older_date)
    else:
        if args.date.count("-") == 2:
            date_format = "%Y-%m-%d"
        else:
            date_format = "%Y-%m-%d-%H:%M:%S"
        date = datetime.strptime(args.date, date_format)
        keep_jobs_from_date(date)

    if args.debug:
        _debug_db_jobs()


def keep_n_most_recent_jobs(n: int):
    print(f"Keeping {n} most recent jobs")
    mc = _get_db()
    db_jobs = mc["jobs"]
    nb_total_jobs = db_jobs.count_documents({})

    if nb_total_jobs <= n:
        print(f"{nb_total_jobs} jobs in database, {n} to keep, nothing to do.")
        return

    # Find jobs to delete.
    # Sort jobs by slurm_last_update ascending
    # and keep only first jobs, excluding n last jobs.
    jobs_to_delete = list(
        db_jobs.find({}).sort([("cw.last_slurm_update", 1)]).limit(nb_total_jobs - n)
    )
    assert len(jobs_to_delete) == nb_total_jobs - n
    # Delete jobs
    filter_to_delete = {"_id": {"$in": [job["_id"] for job in jobs_to_delete]}}
    result = db_jobs.delete_many(filter_to_delete)
    nb_deleted_jobs = result.deleted_count
    # Delete user props associated to deleted jobs
    _delete_user_props(mc, jobs_to_delete)

    nb_remaining_jobs = db_jobs.count_documents({})

    print(
        f"Jobs in database: initially {nb_total_jobs}, deleted {nb_deleted_jobs}, remaining {nb_remaining_jobs}"
    )


def keep_n_most_recent_jobs_per_user(n: int):
    mc = _get_db()
    db_jobs = mc["jobs"]
    nb_total_jobs = db_jobs.count_documents({})

    db_users = mc["users"]
    nb_users = db_users.count_documents({})
    print(f"Keeping {n} most recent jobs for each of {nb_users} users.")

    jobs_to_delete = []
    for user in db_users.find({}).sort([("mila_email_username", 1)]):
        mila_email_username = user["mila_email_username"]
        user_filter = {"cw.mila_email_username": mila_email_username}
        nb_user_jobs = db_jobs.count_documents(user_filter)
        if nb_user_jobs <= n:
            # print(f"[{mila_email_username}] {nb_user_jobs} user jobs, nothing to do.")
            continue

        # Find user jobs to delete.
        # Sort jobs by slurm_last_update ascending
        # and keep only first jobs, excluding n last jobs.
        user_jobs_to_delete = list(
            db_jobs.find(user_filter)
            .sort([("cw.last_slurm_update", 1)])
            .limit(nb_user_jobs - n)
        )
        assert len(user_jobs_to_delete) == nb_user_jobs - n
        jobs_to_delete.extend(user_jobs_to_delete)
        # print(f"[{mila_email_username}] {nb_user_jobs} user jobs, {len(user_jobs_to_delete)} to delete.")

    if not jobs_to_delete:
        print(f"Each user has at most {n} jobs, nothing to do.")
        return

    filter_to_delete = {"_id": {"$in": [job["_id"] for job in jobs_to_delete]}}
    result = db_jobs.delete_many(filter_to_delete)
    nb_deleted_jobs = result.deleted_count
    # Delete user props associated to deleted jobs
    _delete_user_props(mc, jobs_to_delete)

    nb_remaining_jobs = db_jobs.count_documents({})

    print(
        f"Jobs in database: initially {nb_total_jobs}, deleted {nb_deleted_jobs}, remaining {nb_remaining_jobs}"
    )


def keep_jobs_from_date(date: datetime):
    print(f"Keeping jobs updated since: {date}")
    mc = _get_db()
    db_jobs = mc["jobs"]
    nb_total_jobs = db_jobs.count_documents({})

    # Find jobs to delete

    jobs_to_delete = list(
        db_jobs.find({"cw.last_slurm_update": {"$lt": date.timestamp()}})
    )
    if not jobs_to_delete:
        print(f"No job updated before {date}, nothing to do.")
        return

    # Delete jobs
    filter_to_delete = {"_id": {"$in": [job["_id"] for job in jobs_to_delete]}}
    result = db_jobs.delete_many(filter_to_delete)
    nb_deleted_jobs = result.deleted_count
    # Delete user props associated to deleted jobs
    _delete_user_props(mc, jobs_to_delete)

    nb_remaining_jobs = db_jobs.count_documents({})

    print(
        f"Jobs in database: initially {nb_total_jobs}, deleted {nb_deleted_jobs}, remaining {nb_remaining_jobs}"
    )


def _delete_user_props(mc, jobs: list):
    """Delete user props associated to given jobs."""
    # Build filter.
    # Use OR, to delete any of given jobs.
    filter_jobs = {
        "$or": [
            # For each job, find user prop with same job ID and cluster name.
            {
                "$and": [
                    {"job_id": job["slurm"]["job_id"]},
                    {"cluster_name": job["slurm"]["cluster_name"]},
                ]
            }
            for job in jobs
        ]
    }

    result = mc["job_user_props"].delete_many(filter_jobs)
    return result.deleted_count


def _get_db():
    client = get_mongo_client()
    mc = client[get_config("mongo.database_name")]
    return mc


def _debug_db_jobs():
    """Debug function. Print job ID and `last_slurm_update` for each job in database."""
    mc = _get_db()
    db_jobs = mc["jobs"]
    jobs = list(db_jobs.find({}).sort([("cw.last_slurm_update", 1)]))
    nb_jobs = len(jobs)
    print(f"[JOBS: {nb_jobs}]")
    for i, job in enumerate(jobs):
        print(
            f"\t[{i + 1}/{nb_jobs}] job_id={job['slurm']['job_id']} cw.last_slurm_update={_fmt_last_slurm_update(job)}"
        )


def _fmt_last_slurm_update(job):
    """Pretty print last_slurm_update (None if None, else as a date time)."""
    v = job["cw"].get("last_slurm_update")
    if v is None:
        return v
    return datetime.fromtimestamp(v)


if __name__ == "__main__":
    main(sys.argv[1:])
