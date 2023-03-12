"""
This script is solely for use with "dev.sh" when we
want to test out certain features of the front-end
and we need to have some semblance of jobs in there.

It is not used by the test suite, nor is it being used in production.
It uses the module `test_common`, which might look like bad design
because functionality for running tests shouldn't be used by the
actual non-test modules themselves, but it's just a convenience
to avoid something even messier.

This script also modifies some job status to make them
more diverse for the purposes of trying out the functionality
in the web-front end. It does lead to some absurdity with
some pending jobs having a start/end time and things like that.
In that regards, this ends up with fake_data that's slightly
different when we run this script in the context of "dev.sh"
than when pytest runs with "test.sh" and loads the fake data
without messing around with the job status.
"""

import argparse
import sys
import json
from datetime import datetime
import os

from clockwork_web.config import register_config
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config
from test_common.fake_data import mutate_some_job_status, populate_fake_data


def store_data_in_db(data_json_file=None):
    # Open the database and insert the contents.
    client = get_mongo_client()
    populate_fake_data(
        client[get_config("mongo.database_name")], json_file=data_json_file
    )


def modify_timestamps(data):
    """
    This function updates the timestamps in order to simulate jobs which have
    been launched more recently than they were.
    """
    # Retrieve the most recent timestamp (ie its end_time)
    most_recent_timestamp = data["jobs"][0]["slurm"]["end_time"]
    # most_recent_timestamp = min(job["slurm"]["end_time"] for job in data["jobs"])
    for job in data["jobs"]:
        new_end_time = job["slurm"]["end_time"]
        if new_end_time:
            if new_end_time > most_recent_timestamp:
                most_recent_timestamp = new_end_time

    # Retrieve the time interval between this timestamp and now
    time_delta = datetime.now().timestamp() - most_recent_timestamp

    # Substract it to the timestamps of the jobs
    for job in data["jobs"]:
        if job["slurm"]["submit_time"]:
            job["slurm"]["submit_time"] += time_delta
        if job["slurm"]["start_time"]:
            job["slurm"]["start_time"] += time_delta
        if job["slurm"]["end_time"]:
            job["slurm"]["end_time"] += time_delta


def main(argv):
    # Retrieve the arguments passed to the script
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recent",
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Modify the timestamps of the jobs in order to simulate more recent jobs if this argument is provided.",
    )
    args = parser.parse_args(argv[1:])

    # Register the elements to access the database
    register_config("mongo.connection_string", "")
    register_config("mongo.database_name", "clockwork")

    if args.recent:
        # Load the fake data as a JSON dictionary.
        # Understandably, this absolute path refers to something
        # in the Docker container launched by dev.sh.
        input_file = "/clockwork/test_common/fake_data.json"
        with open(input_file, "r") as infile:
            fake_data = json.load(infile)

        # Simulate recent timestamps on the jobs data
        modify_timestamps(fake_data)

        # Simulate status for the jobs
        mutate_some_job_status(fake_data)

        # Write the data in a JSON file
        with open("/clockwork/test_common/tmp.json", "w+") as outfile:
            json.dump(fake_data, outfile, indent=2)

        # Store the modified fake_data in the database
        store_data_in_db(data_json_file="/clockwork/test_common/tmp.json")

    else:
        # Store the generated fake data in the database
        store_data_in_db()


if __name__ == "__main__":
    main(sys.argv)
