import os

import argparse
import itertools
import sys
import logging
import time
from datetime import datetime, timedelta
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


log_format = "%(levelname)s:%(name)s:%(asctime)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)

logger = logging.getLogger("server_benchmark")


class CallStat(
    namedtuple(
        "CallStat", ("username", "nb_jobs", "pt_start", "pt_end", "pc_start", "pc_end")
    )
):
    """
    Class to collect stats and time for 1 request.

    Python provides 2 precision functions for profiling:
    - time.process_time_ns(): only process time, does not include sleep times.
    - time.perf_counter_ns(): includes sleep times.

    I made a mistake in previous commits because I measured requests using
    process_time(). Thus, request times looked very small, as they don't
    include sleeps, which are used to wait for server response.

    So, I decided to measure both process time and full (perf_counter) time
    to check how they differ:
    - process time is still very small (less than 0.10 seconds)
      and correctly approximated with a linear regression wr/t nunber of jobs.
    - full time (perf_counter) is very much higher, sometimes up to 10 seconds,
      and way more irregular (badly approximated with linear regression).

    In practice, I guess the relevant measure is full time (with perf_counter),
    as it correctly represents how much time user could wait to get response
    ** if he gets all jobs at once without pagination **.
    """

    @property
    def pt_nanoseconds(self):
        """Duration measured with process time."""
        return self.pt_end - self.pt_start

    @property
    def pc_nanoseconds(self):
        """Duration measured with perf counter (full duration)."""
        return self.pc_end - self.pc_start


# Class to collect stats and time for a batch of requests.
# `calls` is a list of CallStat.
# `nanoseconds` is duration for all requests, measured with time.perf_counter_ns().
GroupStat = namedtuple("GroupStat", ("calls", "nanoseconds"))


class BenchmarkClient(ClockworkToolsClient):
    """Client with a specific method for profiling."""

    def profile_getting_user_jobs(self, username: str) -> CallStat:
        """Profile a request `jobs/list` with given username and return a CallStat."""
        pc_start = time.perf_counter_ns()
        pt_start = time.process_time_ns()
        jobs = self.jobs_list(username)
        pt_end = time.process_time_ns()
        pc_end = time.perf_counter_ns()
        return CallStat(
            username=username,
            nb_jobs=len(jobs),
            pc_start=pc_start,
            pc_end=pc_end,
            pt_start=pt_start,
            pt_end=pt_end,
        )


class Stats:
    """Helper class to make stats."""

    @staticmethod
    def benchmark_stats(stats: List[GroupStat], bench_date, working_directory="."):
        """Function to generate stats from benchmark output.

        Currently:
        - just display a plot for request duration relative to number of jobs returned per request.
        - Compute linear regression, to estimate request duration wr/t number of jobs returned per request.

        Plot is saved in working directory.
        """

        nb_jobs = []
        pt_seconds = []
        pc_seconds = []
        job_len_to_usernames = {}
        for group_stat in stats:
            for cs in group_stat.calls:
                nb_jobs.append(cs.nb_jobs)
                pt_seconds.append(cs.pt_nanoseconds / 1e9)
                pc_seconds.append(cs.pc_nanoseconds / 1e9)
                job_len_to_usernames.setdefault(cs.nb_jobs, set()).add(cs.username)

        min_jobs = min(nb_jobs)
        max_jobs = max(nb_jobs)
        usernames_with_min_jobs = sorted(job_len_to_usernames[min_jobs])
        usernames_with_max_jobs = sorted(job_len_to_usernames[max_jobs])
        logger.info(
            f"Nb. of jobs returned per request from {min_jobs} to {max_jobs}, "
            f"average {Stats._average(nb_jobs)}."
        )
        logger.info(
            f"Usernames with {min_jobs} jobs: {', '.join(usernames_with_min_jobs)}"
        )
        logger.info(
            f"Usernames with {max_jobs} jobs: {', '.join(usernames_with_max_jobs)}"
        )
        # Draw a plot for seconds measured with process time.
        Stats._plots_seconds_per_nb_jobs(
            nb_jobs, pt_seconds, working_directory, bench_date, "process_time"
        )
        # Draw another plot for seconds measured with perf_counter.
        Stats._plots_seconds_per_nb_jobs(
            nb_jobs, pc_seconds, working_directory, bench_date, "perf_counter"
        )

    @staticmethod
    def _plots_seconds_per_nb_jobs(
        nb_jobs, seconds, working_directory, bench_date, prefix
    ):
        """Draw plot with nb_jobs (x) and seconds (y)."""
        logger.info(f"[{prefix}]")
        logger.info(
            f"Request duration from {min(seconds)} to {max(seconds)} seconds, "
            f"average {Stats._average(seconds)} seconds."
        )
        a, b, r = Stats.linear_regression(nb_jobs, seconds)
        logger.info(
            f"Linear regression: request duration = {a} * nb_jobs + {b}, with correlation r = {r}"
        )
        logger.info(
            f"Estimated request duration for 1 returned job is {a + b} seconds."
        )

        # Plot request duration per number of jobs
        fig, ax = plt.subplots()
        ax.plot(
            [min(nb_jobs), max(nb_jobs)], [a * min(nb_jobs) + b, a * max(nb_jobs) + b]
        )
        ax.scatter(nb_jobs, seconds)

        plt.title(f"[{prefix}] {len(seconds)} total requests, {bench_date}")
        plt.xlabel("Number of jobs returned by request")
        plt.ylabel("Request duration in seconds")
        plot_file_path = os.path.join(
            working_directory, f"bench_{bench_date}_plot_{prefix}.jpg"
        )
        plt.savefig(plot_file_path, bbox_inches="tight")
        logger.info(f"Saved plot image at: {plot_file_path}")
        # If both saving and showing, save before, show after, otherwise saved image will be blank.
        # ref (2023/03/30): https://stackoverflow.com/a/9890599
        # plt.show()
        plt.close(fig)

    @staticmethod
    def linear_regression(x, y):
        avg_x = Stats._average(x)
        avg_y = Stats._average(y)
        cov_xy = Stats._covariance(x, y)
        v_x = Stats._variance(x)
        v_y = Stats._variance(y)
        a = cov_xy / v_x
        b = avg_y - a * avg_x
        r = cov_xy / ((v_x * v_y) ** 0.5)
        return a, b, r

    @staticmethod
    def _covariance(values_x: List, values_y: List):
        assert len(values_x) == len(values_y)
        avg_x = Stats._average(values_x)
        avg_y = Stats._average(values_y)
        return sum((x - avg_x) * (y - avg_y) for x, y in zip(values_x, values_y)) / len(
            values_x
        )

    @staticmethod
    def _variance(values: List):
        avg_x = Stats._average(values)
        return sum(x**2 for x in values) / len(values) - avg_x**2

    @staticmethod
    def _average(values: List):
        return sum(values) / len(values)


def raise_exception(exc):
    """Error callback, used to raise exceptions from processes."""
    raise exc


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(
        prog=argv[0],
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
Benchmark for server.

Send one request `jobs/list` for each user in <--processes> parallel processes until reaching <--time> seconds.
""".strip(),
    )
    parser.add_argument("-a", "--address", help="Server host.")
    parser.add_argument("-p", "--port", type=int, default=443, help="Server port.")
    parser.add_argument(
        "--config",
        type=str,
        help=(
            "Optional JSON configuration file to use for benchmarking. "
            "If not specified, use --address, --port, and OS environment variables for clockwork api key and email. "
            "If file exists, ignore --address, --port and OS variables, and read config from file. "
            "If file does not exist, create file with config values from --address, --port and OS variables. "
            "Configuration file must contain a dictionary with keys "
            "'address' (str), 'port` (int), 'api_key` (str), 'email' (str), "
            "and optional 'users' (list of str)."
        ),
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=60,
        help="Time to run benchmark (default 60 seconds).",
    )
    parser.add_argument(
        "-c",
        "--processes",
        type=int,
        default=os.cpu_count(),
        help="Number of parallel processes to use to send requests (default to number of CPU cores)",
    )
    args = parser.parse_args(argv[1:])
    print("Arguments:", args)

    if args.time < 1:
        logger.error(f"No positive time specified for benchmarking, exit.")
        sys.exit(1)

    bench_date = datetime.now()
    config_path = None
    working_directory = "."
    if args.config:
        config_path = os.path.abspath(args.config)
        working_directory = os.path.dirname(config_path)
        # Save next log messages into a file.
        log_formatter = logging.Formatter(log_format)
        log_path = os.path.join(working_directory, f"bench_{bench_date}.log")
        logger.info(f"Saving log in: {log_path}")
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

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
        if not address:
            logger.error(
                "Either --address <port> or --config <file.json> (with existing file) is required."
            )
            sys.exit(1)

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

    nb_processes = args.processes or os.cpu_count()
    logger.info(f"Benchmark starting, using {nb_processes} processes.")

    # Create an infinite iterator to provide usernames as long as needed.
    infinite_users = itertools.cycle(users)
    # Use a list to collect request call stats.
    outputs: List[CallStat] = []
    # Timeout in nanoseconds.
    timeout = args.time * 1e9
    start = time.perf_counter_ns()
    # Submit asynchronous requests as long as
    # elapsed time since `start` does not reach timeout,
    # and terminate() as soon as possible when timeout is reached.
    with multiprocessing.Pool(processes=nb_processes) as p:
        while time.perf_counter_ns() - start < timeout:
            p.apply_async(
                client.profile_getting_user_jobs,
                args=(next(infinite_users),),
                callback=outputs.append,
                error_callback=raise_exception,
            )
        p.terminate()
    group_stat = GroupStat(calls=outputs, nanoseconds=time.perf_counter_ns() - start)

    duration_seconds = group_stat.nanoseconds / 1e9
    nb_reqs_per_sec = len(outputs) / duration_seconds
    nb_reqs_per_min = nb_reqs_per_sec * 60
    nb_reqs_in_5min = nb_reqs_per_min * 5
    logger.info(
        f"Sent {len(outputs)} requests in {duration_seconds} seconds ({timedelta(seconds=duration_seconds)})."
    )
    logger.info("Average:")
    logger.info(f"{nb_reqs_per_sec} requests per second.")
    logger.info(f"{nb_reqs_per_min} requests per minute.")
    logger.info(f"{nb_reqs_in_5min} requests per 5 minutes.")

    Stats.benchmark_stats(
        [group_stat], working_directory=working_directory, bench_date=bench_date
    )
    logger.info("End.")


if __name__ == "__main__":
    main()
