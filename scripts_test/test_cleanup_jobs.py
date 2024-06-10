import pytest

from pymongo import MongoClient
from scripts.cleanup_jobs import main as cleanup_jobs
from scripts_test.config import get_config
from datetime import datetime, timedelta


class CleanupTestContext:
    """
    Helper to test job cleanup script.

    Create and fill a test database.
    """

    NB_JOBS = 100

    def __init__(self):
        db_name = get_config("mongo.database_name")
        client = MongoClient(get_config("mongo.connection_string"))
        mc = client[db_name]

        base_datetime = datetime.now()

        # Create fake jobs
        fake_jobs = [
            {
                "slurm": {"job_id": str(i)},
                "cw": {
                    "last_slurm_update": (base_datetime + timedelta(days=i)).timestamp()
                },
            }
            for i in range(self.NB_JOBS)
        ]
        # Unset `last_slurm_update` for 2 first jobs.
        del fake_jobs[0]["cw"]["last_slurm_update"]
        fake_jobs[1]["cw"]["last_slurm_update"] = None

        db_jobs = mc["jobs"]
        db_jobs.delete_many({})
        db_jobs.insert_many(fake_jobs)
        assert db_jobs.count_documents({}) == self.NB_JOBS

        self.db_name = db_name
        self.base_datetime = base_datetime
        self.mc = mc
        self.db_jobs = db_jobs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mc.drop_collection(self.db_name)
        print("cleaned")

    def get_jobs(self):
        """Get current jobs in test database."""
        jobs = list(self.db_jobs.find({}).sort([("cw.last_slurm_update", 1)]))
        for job in jobs:
            del job["_id"]
        return jobs


def test_keep_n_most_recent_jobs():
    with CleanupTestContext() as ctx:
        jobs = ctx.get_jobs()

        cleanup_jobs(["-n", "500"])
        # There are less than 500 jobs in db, nothing should happen.
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-n", str(CleanupTestContext.NB_JOBS)])
        # There are exactly NB_JOBS jobs in db, nothing should happen.
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-n", "60"])
        # Now db should contain only 60 jobs
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 60
        assert jobs[-60:] == remaining_jobs

        cleanup_jobs(["-n", "60"])
        # There are exactly 60 jobs in db, nothing should happen.
        assert remaining_jobs == ctx.get_jobs()

        cleanup_jobs(["-n", "15"])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 15
        assert jobs[-15:] == remaining_jobs

        cleanup_jobs(["-n", "0"])
        # With current code, "-n 0" will erase all jobs in database.
        assert len(ctx.get_jobs()) == 0


# Parameterize with the two date formats accepted by script `cleanup_jobs`
@pytest.mark.parametrize("date_format", ["%Y-%m-%d-%H:%M:%S", "%Y-%m-%d"])
def test_keep_jobs_after_a_date(date_format):
    with CleanupTestContext() as ctx:
        too_old_date = ctx.base_datetime - timedelta(days=1)
        inbound_date_1 = ctx.base_datetime + timedelta(days=15)
        inbound_date_2 = ctx.base_datetime + timedelta(days=60)
        new_date = ctx.base_datetime + timedelta(days=ctx.NB_JOBS)

        def _fmt_date(d: datetime):
            return d.strftime(date_format)

        jobs = ctx.get_jobs()

        cleanup_jobs(["-d", _fmt_date(too_old_date)])
        # Date is too old, so no job should be deleted
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-d", _fmt_date(inbound_date_1)])
        # In database, 2 jobs don't have last_slurm_update,
        # so these jobs should never be deleted under `-d` argument.
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 100 - (15 - 2)
        assert jobs[:2] + jobs[15:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(inbound_date_2)])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 100 - (60 - 2)
        assert jobs[:2] + jobs[60:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(new_date)])
        # With a date more recent than latest job,
        # all jobs should be deleted, excluding jobs that don't have last_slurm_update.
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 2
        assert jobs[:2] == remaining_jobs
