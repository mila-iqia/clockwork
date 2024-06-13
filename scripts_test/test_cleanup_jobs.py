import pytest

from pymongo import MongoClient
from scripts.cleanup_jobs import main as cleanup_jobs
from scripts_test.config import get_config
from datetime import datetime, timedelta
from collections import Counter


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

        # Create fake users, intended to be checked when cleaning jobs per user.
        fake_users = [
            {"mila_email_username": "first_user_0@email.com"},
            {"mila_email_username": "first_user_1@email.com"},
        ]
        # Create fake jobs
        fake_jobs = [
            {
                "slurm": {"job_id": str(i), "cluster_name": f"cluster_{i}"},
                "cw": {
                    "last_slurm_update": (
                        base_datetime + timedelta(days=i)
                    ).timestamp(),
                    # Associate first NB_JOBS / 4 Jobs to first_user_0 and other jobs to first_user_1
                    "mila_email_username": f"first_user_{int(i >= self.NB_JOBS / 4)}@email.com",
                },
            }
            for i in range(self.NB_JOBS)
        ]
        # Create fake user props, 2 for each job
        fake_user_props = [
            {
                "mila_email_username": f"first_user_{i}@email.com",
                "cluster_name": fake_job["slurm"]["cluster_name"],
                "job_id": fake_job["slurm"]["job_id"],
                "props": {"prop first user 1": "value first user 1"},
            }
            for i, fake_job in enumerate(fake_jobs)
        ] + [
            {
                "mila_email_username": f"second_user_{i}@email.com",
                "cluster_name": fake_job["slurm"]["cluster_name"],
                "job_id": fake_job["slurm"]["job_id"],
                "props": {"prop second user 1": "value second user 1"},
            }
            for i, fake_job in enumerate(fake_jobs)
        ]
        # Unset `last_slurm_update` for 2 first jobs.
        del fake_jobs[0]["cw"]["last_slurm_update"]
        fake_jobs[1]["cw"]["last_slurm_update"] = None

        db_users = mc["users"]
        db_jobs = mc["jobs"]
        db_user_props = mc["job_user_props"]

        db_users.delete_many({})
        db_users.insert_many(fake_users)
        db_jobs.delete_many({})
        db_jobs.insert_many(fake_jobs)
        db_user_props.delete_many({})
        db_user_props.insert_many(fake_user_props)
        assert db_jobs.count_documents({}) == self.NB_JOBS

        self.db_name = db_name
        self.base_datetime = base_datetime
        self.mc = mc
        self.db_jobs = db_jobs
        self.db_user_props = db_user_props

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mc.drop_collection(self.db_name)
        print("cleaned")

    def _get_jobs(self):
        """Get current jobs in test database."""
        jobs = list(self.db_jobs.find({}).sort([("cw.last_slurm_update", 1)]))
        for job in jobs:
            del job["_id"]
        return jobs

    def check_user_props(self) -> list:
        """
        Check that current user props exactly match current jobs in database.

        We expect 2 different user prop dicts per job.

        If everything is ok, return current jobs in database.
        """
        # Get all jobs
        jobs = self._get_jobs()
        # Get all user props
        user_props = list(self.db_user_props.find({}))

        assert len(user_props) == 2 * len(jobs)

        # Map each job to user prop emails.
        user_props_map = {}
        for prop in user_props:
            key = prop["job_id"], prop["cluster_name"]
            user_props_map.setdefault(key, set()).add(prop["mila_email_username"])

        assert len(user_props_map) == len(jobs)
        # Check each job is associated to 2 user props (i.e. 2 emails)
        for job in jobs:
            key = job["slurm"]["job_id"], job["slurm"]["cluster_name"]
            assert key in user_props_map
            assert len(user_props_map[key]) == 2
            # Delete found job in mapping
            del user_props_map[key]
        # At end, mapping should be empty (every job should have been found)
        assert not user_props_map

        # Return jobs for further checks
        return jobs


def test_keep_n_most_recent_jobs():
    with CleanupTestContext() as ctx:
        jobs = ctx.check_user_props()

        cleanup_jobs(["-n", "500"])
        # There are less than 500 jobs in db, nothing should happen.
        assert jobs == ctx.check_user_props()

        cleanup_jobs(["-n", str(CleanupTestContext.NB_JOBS)])
        # There are exactly NB_JOBS jobs in db, nothing should happen.
        assert jobs == ctx.check_user_props()

        cleanup_jobs(["-n", "60"])
        # Now db should contain only 60 jobs
        remaining_jobs = ctx.check_user_props()
        assert len(remaining_jobs) == 60
        assert jobs[-60:] == remaining_jobs

        cleanup_jobs(["-n", "60"])
        # There are exactly 60 jobs in db, nothing should happen.
        assert remaining_jobs == ctx.check_user_props()

        cleanup_jobs(["-n", "15"])
        remaining_jobs = ctx.check_user_props()
        assert len(remaining_jobs) == 15
        assert jobs[-15:] == remaining_jobs

        cleanup_jobs(["-n", "0"])
        # With current code, "-n 0" will erase all jobs in database.
        assert len(ctx.check_user_props()) == 0


def test_keep_n_most_recent_jobs_per_user():
    with CleanupTestContext() as ctx:
        jobs = ctx.check_user_props()

        # Check we indeed have 25 jobs for first_user_0 and 75 jobs for first_user_1
        nb_jobs_per_user = Counter(job["cw"]["mila_email_username"] for job in jobs)
        assert len(nb_jobs_per_user) == 2
        count = nb_jobs_per_user.most_common()
        assert count == [("first_user_1@email.com", 75), ("first_user_0@email.com", 25)]

        cleanup_jobs(["-u", "100"])
        # Nothing should happen
        assert jobs == ctx.check_user_props()

        cleanup_jobs(["-u", "75"])
        # Nothing shoule happen
        assert jobs == ctx.check_user_props()

        cleanup_jobs(["-u", "74"])
        # Nothing should happen for first_user_0 (25 => 25)
        # 1 job (oldest one) should be deleted for first_user_1 (75 => 74)
        current_jobs = ctx.check_user_props()
        jobs_first_user_0 = current_jobs[:25]
        jobs_first_user_1 = current_jobs[25:]
        assert len(jobs_first_user_0) == 25
        assert len(jobs_first_user_1) == 74
        assert all(
            job["cw"]["mila_email_username"] == "first_user_0@email.com"
            for job in jobs_first_user_0
        )
        assert all(
            job["cw"]["mila_email_username"] == "first_user_1@email.com"
            for job in jobs_first_user_1
        )
        assert jobs[:25] == jobs_first_user_0
        assert jobs[26:] == jobs_first_user_1

        cleanup_jobs(["-u", "26"])
        # Nothing should happen for first_user_0 (25 => 25)
        # 74 - 26 jobs (oldest ones) should be deleted for first_user_1 (74 => 26)
        current_jobs = ctx.check_user_props()
        jobs_first_user_0 = current_jobs[:25]
        jobs_first_user_1 = current_jobs[25:]
        assert len(jobs_first_user_0) == 25
        assert len(jobs_first_user_1) == 26
        assert all(
            job["cw"]["mila_email_username"] == "first_user_0@email.com"
            for job in jobs_first_user_0
        )
        assert all(
            job["cw"]["mila_email_username"] == "first_user_1@email.com"
            for job in jobs_first_user_1
        )
        assert jobs[:25] == jobs_first_user_0
        assert jobs[-26:] == jobs_first_user_1

        cleanup_jobs(["-u", "17"])
        # 25 - 17 jobs (oldest ones) should be deleted for first_user_0 (25 => 17)
        # 26 - 17 jobs (oldest ones) should be deleted for first_user_1 (26 => 17)
        current_jobs = ctx.check_user_props()
        jobs_first_user_0 = current_jobs[:17]
        jobs_first_user_1 = current_jobs[17:]
        assert len(jobs_first_user_0) == 17
        assert len(jobs_first_user_1) == 17
        assert all(
            job["cw"]["mila_email_username"] == "first_user_0@email.com"
            for job in jobs_first_user_0
        )
        assert all(
            job["cw"]["mila_email_username"] == "first_user_1@email.com"
            for job in jobs_first_user_1
        )
        assert jobs[(25 - 17) : 25] == jobs_first_user_0
        assert jobs[-17:] == jobs_first_user_1

        cleanup_jobs(["-u", "0"])
        # All jobs should be deleted
        assert len(ctx.check_user_props()) == 0


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

        jobs = ctx.check_user_props()

        cleanup_jobs(["-d", _fmt_date(too_old_date)])
        # Date is too old, so no job should be deleted
        assert jobs == ctx.check_user_props()

        cleanup_jobs(["-d", _fmt_date(inbound_date_1)])
        # In database, 2 jobs don't have last_slurm_update,
        # so these jobs should never be deleted under `-d` argument.
        remaining_jobs = ctx.check_user_props()
        assert len(remaining_jobs) == 100 - (15 - 2)
        assert jobs[:2] + jobs[15:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(inbound_date_2)])
        remaining_jobs = ctx.check_user_props()
        assert len(remaining_jobs) == 100 - (60 - 2)
        assert jobs[:2] + jobs[60:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(new_date)])
        # With a date more recent than latest job,
        # all jobs should be deleted, excluding jobs that don't have last_slurm_update.
        remaining_jobs = ctx.check_user_props()
        assert len(remaining_jobs) == 2
        assert jobs[:2] == remaining_jobs
