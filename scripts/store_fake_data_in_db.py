#!/usr/bin/env python3

import argparse
import sys
import json
from datetime import datetime
import os

from clockwork_web.config import register_config
from clockwork_web.db import init_db, get_db
from clockwork_web.server_app import create_app
from test_common.fake_data import populate_fake_data


def store_data_in_db(data_json_file=None):
    # Create a test context
    app = create_app(extra_config={"TESTING": True, "LOGIN_DISABLED": True})

    # Within this context of tests
    with app.app_context():
        # Initialize the database
        init_db()
        db = get_db()
        # Insert fake data in it
        cf = populate_fake_data(db, json_file=data_json_file)


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


def mutate_some_job_status(data):
    """
    Modifies in place about 1/5 of the job status to get more variations.
    """
    L_status = [
        "COMPLETED",
        "COMPLETING",
        "FAILED",
        "OUT_OF_MEMORY",
        "TIMEOUT",
        "CANCELLED",
        "PREEMPTED",
    ]

    for (i, job) in enumerate(data["jobs"]):
        if i % 30 < len(L_status):
            job["slurm"]["job_state"] = L_status[i % 30]


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
        # Load the fake data as a JSON dictionary
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
