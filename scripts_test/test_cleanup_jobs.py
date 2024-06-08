import pytest

from pymongo import MongoClient
from scripts.cleanup_jobs import main as cleanup_jobs
from scripts_test.config import get_config
from datetime import datetime, timedelta


class DummyContext:
    DUMMY_DB_NAME = "testing_db_for_cleanup_1234"
    NB_JOBS = 100

    def __init__(self):
        client = MongoClient(get_config("mongo.connection_string"))
        mc = client[get_config("mongo.database_name")]

        base_datetime = datetime.now()

        fake_jobs = [
            {
                "slurm": {"job_id": str(i)},
                "cw": {
                    "last_slurm_update": (base_datetime + timedelta(days=i)).timestamp()
                },
            }
            for i in range(self.NB_JOBS)
        ]
        del fake_jobs[0]["cw"]["last_slurm_update"]
        fake_jobs[1]["cw"]["last_slurm_update"] = None

        db_jobs = mc["jobs"]
        db_jobs.delete_many({})
        db_jobs.insert_many(fake_jobs)
        assert db_jobs.count_documents({}) == self.NB_JOBS
        print(db_jobs.count_documents({}))

        self.base_datetime = base_datetime
        self.mc = mc
        self.db_jobs = db_jobs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mc.drop_collection(self.DUMMY_DB_NAME)
        print("cleaned")

    def get_jobs(self):
        jobs = list(self.db_jobs.find({}).sort([("cw.last_slurm_update", 1)]))
        for job in jobs:
            del job["_id"]
        return jobs


def test_keep_n_most_recent_jobs():
    with DummyContext() as ctx:
        jobs = ctx.get_jobs()

        cleanup_jobs(["-n", "500"])
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-n", str(DummyContext.NB_JOBS)])
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-n", "60"])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 60
        assert jobs[-60:] == remaining_jobs

        cleanup_jobs(["-n", "60"])
        assert remaining_jobs == ctx.get_jobs()

        cleanup_jobs(["-n", "15"])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 15
        assert jobs[-15:] == remaining_jobs

        cleanup_jobs(["-n", "0"])
        assert len(ctx.get_jobs()) == 0


@pytest.mark.parametrize("date_format", ["%Y-%m-%d-%H:%M:%S", "%Y-%m-%d"])
def test_keep_jobs_after_a_date(date_format):
    with DummyContext() as ctx:
        too_old_date = ctx.base_datetime - timedelta(days=1)
        inbound_date_1 = ctx.base_datetime + timedelta(days=15)
        inbound_date_2 = ctx.base_datetime + timedelta(days=60)
        new_date = ctx.base_datetime + timedelta(days=ctx.NB_JOBS)

        def _fmt_date(d: datetime):
            return d.strftime(date_format)

        jobs = ctx.get_jobs()

        cleanup_jobs(["-d", _fmt_date(too_old_date)])
        assert jobs == ctx.get_jobs()

        cleanup_jobs(["-d", _fmt_date(inbound_date_1)])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 100 - (15 - 2)
        assert jobs[:2] + jobs[15:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(inbound_date_2)])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 100 - (60 - 2)
        assert jobs[:2] + jobs[60:] == remaining_jobs

        cleanup_jobs(["-d", _fmt_date(new_date)])
        remaining_jobs = ctx.get_jobs()
        assert len(remaining_jobs) == 2
        assert jobs[:2] == remaining_jobs
