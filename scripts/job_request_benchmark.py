import os

import argparse
import sys
import logging
import time
from datetime import datetime
from collections import namedtuple
import json

try:
    from clockwork_tools.client import ClockworkToolsClient
except Exception:
    print(
        "Clockwork tools needed. You can install it with `cd clockwork_tools` then `pip install -e .`"
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

    def summary(self):
        return {
            "nb_jobs": self.nb_jobs,
            "pc_nanoseconds": self.pc_nanoseconds,
        }


class BenchmarkClient(ClockworkToolsClient):
    """Client with a specific method for profiling."""

    def profile_getting_user_jobs(self, username: str = None) -> CallStat:
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


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(
        prog=argv[0],
        formatter_class=argparse.RawTextHelpFormatter,
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
            "'address' (str), 'port` (int), 'api_key` (str), 'email' (str)."
        ),
    )
    parser.add_argument(
        "-n",
        "--nb-requests",
        type=int,
        default=10,
        help="Number of requests to send (default, 10).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Benchmark name, used to save stats on disk. "
        "Saved in <working directory>/<output>.json",
    )
    args = parser.parse_args(argv[1:])
    print("Arguments:", args)

    if args.nb_requests < 1:
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
        log_path = os.path.join(working_directory, f"bench_{args.output}.log")
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
        logger.info(f"Loaded config from file: address: {address}, port: {port}")
    else:
        address = args.address
        port = args.port
        # API key and email will be retrieved from OS environment in client constructor.
        api_key = None
        email = None
        if not address:
            logger.error(
                "Either --address <port> or --config <file.json> (with existing file) is required."
            )
            sys.exit(1)

    client = BenchmarkClient(
        host=address, port=port, clockwork_api_key=api_key, email=email
    )

    output = []
    for i in range(args.nb_requests):
        cs = client.profile_getting_user_jobs()
        logger.info(
            f"[{i + 1}] Sent request for username in {cs.pc_nanoseconds / 1e9} seconds, "
            f"received {cs.nb_jobs} jobs."
        )
        output.append(cs.summary())

    if config_path and not os.path.exists(config_path):
        # If args.config is defined, we save config file  if args.config does not exist.
        config = {
            "address": client.host,
            "port": client.port,
            "api_key": client.clockwork_api_key,
            "email": client.email,
        }
        with open(config_path, "w") as file:
            json.dump(config, file)
        logger.info(f"Saved config file at: {config_path}")

    output_path = os.path.join(working_directory, f"{args.output}.json")
    with open(output_path, "w") as file:
        json.dump(output, file)
        logger.info(f"Saved stats at: {output_path}")
    logger.info("End.")


if __name__ == "__main__":
    main()
