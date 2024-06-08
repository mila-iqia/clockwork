import argparse
import sys
from datetime import datetime
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config


def _get_db():
    client = get_mongo_client()
    mc = client[get_config("mongo.database_name")]
    return mc


def keep_n_most_recent_jobs(n: int):
    print(f"Keeping {n} most recent jobs")
    mc = _get_db()
    db_jobs = mc["jobs"]
    nb_total_jobs = db_jobs.count_documents({})

    if nb_total_jobs <= n:
        print(f"{nb_total_jobs} jobs in database, {n} to keep, nothing to do.")
        return

    jobs_to_delete = list(
        db_jobs.find({}).sort([("cw.last_slurm_update", 1)]).limit(nb_total_jobs - n)
    )
    assert len(jobs_to_delete) == nb_total_jobs - n
    filter_to_delete = {"_id": {"$in": [job["_id"] for job in jobs_to_delete]}}

    result = db_jobs.delete_many(filter_to_delete)
    nb_deleted_jobs = result.deleted_count

    nb_remaining_jobs = db_jobs.count_documents({})

    print(
        f"Jobs in database: initially {nb_total_jobs}, deleted {nb_deleted_jobs}, remaining {nb_remaining_jobs}"
    )


def keep_jobs_from_date(date: datetime):
    print(f"Keeping jobs starting from: {date}")
    mc = _get_db()
    db_jobs = mc["jobs"]
    nb_total_jobs = db_jobs.count_documents({})

    result = db_jobs.delete_many({"cw.last_slurm_update": {"$lt": date.timestamp()}})
    nb_deleted_jobs = result.deleted_count

    nb_remaining_jobs = db_jobs.count_documents({})

    print(
        f"Jobs in database: initially {nb_total_jobs}, deleted {nb_deleted_jobs}, remaining {nb_remaining_jobs}"
    )


def _debug_db_jobs():
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
    v = job["cw"].get("last_slurm_update")
    if v is None:
        return v
    return datetime.fromtimestamp(v)


def main(arguments: list):
    parser = argparse.ArgumentParser(description="Delete old jobs from database.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-n",
        "--jobs",
        type=int,
        help=(
            "Number of most recent jobs to keep. If specified, script will delete all older jobs until N jobs remain. "
            "If there was initially less than N jobs in database, nothing will be deleted."
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
    else:
        if args.date.count("-") == 2:
            date_format = "%Y-%m-%d"
        else:
            date_format = "%Y-%m-%d-%H:%M:%S"
        date = datetime.strptime(args.date, date_format)
        keep_jobs_from_date(date)

    if args.debug:
        _debug_db_jobs()


if __name__ == "__main__":
    main(sys.argv[1:])
