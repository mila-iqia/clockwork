import os

from clockwork_tools.client import ClockworkToolsClient
import argparse
import sys
import logging
import time
from datetime import timedelta
import multiprocessing

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s:%(name)s:%(asctime)s: %(message)s"
)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server_benchmark")


SLEEP_SECONDS = 30


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Test server load capacity and make a benchmark for server response.",
    )
    parser.add_argument("-a", "--address", required=True, help="Server host.")
    parser.add_argument("-p", "--port", type=int, default=443, help="Server port.")
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=300,
        help="total benchmarking time (in seconds). Script will send requests every 30 seconds within this time.",
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        help="Number of requests to send each 30 seconds. Default is number of available users.",
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

    client = ClockworkToolsClient(host=args.address, port=args.port)

    jobs = client.jobs_list()
    logger.info(f"Initial number of jobs: {len(jobs)}")
    # Get and sort users. Remove `None`, because a job may have no user.
    users = sorted({job["cw"]["mila_email_username"] for job in jobs} - {None})
    logger.info(f"Number of users: {len(users)}")
    if not users:
        # Use user "None" if no user available.
        # With None user, request `jobs/list` will list all available jobs.
        users = [None]
        logger.warning(
            "No user found, each request `jobs/list` will list all available jobs."
        )

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

    nb_processes = args.threads or os.cpu_count()
    logger.info(f"Benchmark starting, using {nb_processes} processes.")
    start_time = time.perf_counter_ns()
    while True:
        prev_time = time.perf_counter_ns()
        with multiprocessing.Pool(processes=nb_processes) as p:
            results = list(p.imap_unordered(client.jobs_list, requested_users))
        current_time = time.perf_counter_ns()

        # Just check we really get some jobs
        assert sum(len(result) for result in results)

        logger.info(
            f"Sent {len(requested_users)} requests in {(current_time - prev_time) / 1e9} seconds."
        )
        total_duration = (current_time - start_time) / 1e9
        if args.time < SLEEP_SECONDS or total_duration >= args.time:
            break
        time.sleep(SLEEP_SECONDS)
    elapsed = timedelta(seconds=total_duration)
    logger.info(f"Terminated, elapsed {elapsed} ({total_duration} seconds)")


if __name__ == "__main__":
    main()
