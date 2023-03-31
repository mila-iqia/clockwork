import os

import argparse
import sys
import logging
import time
from datetime import timedelta
from typing import List
import multiprocessing
from collections import namedtuple
import json

try:
    from clockwork_tools.client import ClockworkToolsClient
except Exception:
    print(
        "Clockwork tools needed. You can install it with `cd clockwork_tools` then `pip install -e .`"
    )
    raise

try:
    import matplotlib.pyplot as plt
except Exception:
    print(
        "Matplotlib needed. You can install it with `pip install matplotlib`",
        file=sys.stderr,
    )
    raise

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s:%(name)s:%(asctime)s: %(message)s"
)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server_benchmark")


# Time to wait for between two batches of requests sent to server.
SLEEP_SECONDS = 30

# Class to collect stats and time for 1 request.
CallStat = namedtuple("CallStat", ("nb_jobs", "nanoseconds"))

# Class to collect stats and time for a batch of requests.
# `calls` is a list of CallStat.
GroupStat = namedtuple("GroupStat", ("calls", "nanoseconds"))


class BenchmarkClient(ClockworkToolsClient):
    """Client with a specific method for profiling."""

    def profile_getting_user_jobs(self, username: str) -> CallStat:
        """Profile a request `jobs/list` with given username and return a CallStat."""
        prev_time = time.process_time_ns()
        jobs = self.jobs_list(username)
        post_time = time.process_time_ns()
        return CallStat(nb_jobs=len(jobs), nanoseconds=post_time - prev_time)


def make_stats(stats: List[GroupStat], working_directory="."):
    """Function to generate stats from benchmark output."""
    # Currently just display a plot with
    # request time relative to number of jobs returned by request.
    # Plot is saved in given working directory.
    nb_jobs = []
    nanoseconds = []
    for group_stat in stats:
        for cs in group_stat.calls:
            nb_jobs.append(cs.nb_jobs)
            nanoseconds.append(cs.nanoseconds / 1e9)
    fig, ax = plt.subplots()
    ax.scatter(nb_jobs, nanoseconds)
    plt.xlabel("Number of jobs returned by request")
    plt.ylabel("Request time in seconds")
    plot_file_path = os.path.join(working_directory, "nb_jobs_to_request_time.jpg")
    plt.savefig(plot_file_path, bbox_inches="tight")
    logger.info(f"Saved plot image at: {plot_file_path}")
    # If both saving and showing, save before, show after, otherwise saved image will be blank.
    # ref (2023/03/30): https://stackoverflow.com/a/9890599
    # plt.show()
    plt.close(fig)


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Test server load capacity and make a benchmark for server response.",
    )
    parser.add_argument("-a", "--address", required=True, help="Server host.")
    parser.add_argument("-p", "--port", type=int, default=443, help="Server port.")
    parser.add_argument(
        "--config",
        type=str,
        help=(
            "Optional JSON configuration file to use for benchmarking. "
            "If not specified, use --address, --port, and OS environment variables for clockwork api key and email. "
            "Else if file exists, ignore --address, --port and OS variables, and read config from file. "
            "Else If file does not exist, create file with config values from --address, --port and OS variables. "
            "Configuration file must contain a dictionary with keys "
            "'address' (str), 'port` (int), 'api_key` (str), 'email' (str), "
            "and optional 'users' (list of str)."
        ),
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=300,
        help=(
            f"total benchmarking time (in seconds). "
            f"Script will send requests every {SLEEP_SECONDS} seconds within this time."
        ),
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        help=f"Number of requests to send each {SLEEP_SECONDS} seconds. Default is number of available users.",
    )
    parser.add_argument(
        "-c",
        "--threads",
        type=int,
        default=os.cpu_count(),
        help="Number of parallel processes to use to send requests",
    )
    args = parser.parse_args(argv[1:])
    print("Arguments:", args)

    if args.time < 1:
        logger.error(f"No positive time specified for benchmarking, exit.")
        sys.exit(1)

    config_path = None
    working_directory = "."
    if args.config:
        config_path = os.path.abspath(args.config)
        working_directory = os.path.dirname(config_path)

    if config_path and os.path.isfile(config_path):
        # Read config file if available.
        with open(config_path) as file:
            config = json.load(file)
        address = config["address"]
        port = config["port"]
        api_key = config["api_key"]
        email = config["email"]
        users = config.get("users", [])
        logger.info(
            f"Loaded config from file: address: {address}, port: {port}, users: {len(users) or 'not found'}"
        )
    else:
        address = args.address
        port = args.port
        # API key and email will be retrieved from OS environment in client constructor.
        api_key = None
        email = None
        users = []

    client = BenchmarkClient(
        host=address, port=port, clockwork_api_key=api_key, email=email
    )

    to_save_users = False
    if not users:
        logger.info("Collecting jobs to get users ...")
        jobs = client.jobs_list()
        logger.info(f"Initial number of jobs: {len(jobs)}")
        # Get and sort users. Remove `None`, because a job may have no user.
        users = sorted({job["cw"]["mila_email_username"] for job in jobs} - {None})
        to_save_users = True

    logger.info(f"Number of users: {len(users)}")
    if not users:
        # Use user "None" if no user available.
        # With None user, request `jobs/list` will list all available jobs.
        users = [None]
        logger.warning(
            "No user found, each request `jobs/list` will list all available jobs (using user `None`)."
        )

    if config_path and (to_save_users or not os.path.exists(config_path)):
        # If args.config is defined, we save config file
        # either if args.config does not exist,
        # or if we collected new users.
        config = {
            "address": client.host,
            "port": client.port,
            "api_key": client.clockwork_api_key,
            "email": client.email,
            "users": users,
        }
        with open(config_path, "w") as file:
            json.dump(config, file)
        logger.info(f"Saved config file at: {config_path}")

    if args.requests is None or args.requests == len(users):
        requested_users = users
        logger.info(f"Will send requests for available {len(requested_users)} users.")
    elif args.requests < len(users):
        requested_users = users[: args.requests]
        logger.info(f"Will send requests for only {len(requested_users)} users.")
    else:
        nb_repeats = args.requests // len(users)
        nb_supplementary = args.requests % len(users)
        requested_users = (users * nb_repeats) + users[:nb_supplementary]
        logger.info(
            f"Will send requests for {len(requested_users)} users (repeated from {len(users)} available users)."
        )

    global_stats: List[GroupStat] = []
    nb_processes = args.threads or os.cpu_count()
    logger.info(f"Benchmark starting, using {nb_processes} processes.")
    start_time = time.perf_counter_ns()
    while True:
        prev_time = time.perf_counter_ns()
        with multiprocessing.Pool(processes=nb_processes) as p:
            local_stats = list(
                p.imap_unordered(client.profile_getting_user_jobs, requested_users)
            )
        current_time = time.perf_counter_ns()
        group_stat = GroupStat(calls=local_stats, nanoseconds=current_time - prev_time)
        global_stats.append(group_stat)

        # Just check we really get some jobs
        assert sum(cs.nb_jobs for cs in group_stat.calls)

        logger.info(
            f"Sent {len(requested_users)} requests in {group_stat.nanoseconds / 1e9} seconds."
        )
        total_duration = (current_time - start_time) / 1e9
        if args.time < SLEEP_SECONDS or total_duration >= args.time:
            break
        time.sleep(SLEEP_SECONDS)

    logger.info(
        f"Terminated, elapsed {timedelta(seconds=total_duration)} ({total_duration} seconds)"
    )
    make_stats(global_stats, working_directory=working_directory)


if __name__ == "__main__":
    main()
