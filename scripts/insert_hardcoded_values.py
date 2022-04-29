"""
Some tests require hardcoded values in the resulting fake data. Thus, this
script is used to insert them in the JSON containing the fake data.
"""

import argparse
import json
import os
import sys


def get_jobs_hardcoded_values():
    """
    Returns the hardcoded data to be inserted in the jobs list of the fake data.
    """
    return [
        {
            "slurm": {
                "job_id": "284357",
                "name": "somejobname_143485",
                "cc_account_username": "ccuser01",
                "uid": 10001,
                "account": "def-pomme-rrg",
                "job_state": "PENDING",
                "exit_code": "0:0",
                "time_limit": 864000,
                "submit_time": 1629920255.0,
                "start_time": None,
                "end_time": None,
                "partition": "fun_partition",
                "nodes": None,
                "num_nodes": "1",
                "num_cpus": "4",
                "num_tasks": "1",
                "cpus_per_task": "4",
                "TRES": "cpu=4,mem=16G,node=1,billing=4",
                "command": "/a22/b841/c601",
                "work_dir": "/a957/b470/c215",
                "stderr": "/a284/b903/c481.err",
                "stdin": "/dev/null",
                "stdout": "/a728/b781/c844.out",
                "cluster_name": "graham",
            },
            "cw": {"mila_email_username": None},
            "user": {},
        }
    ]


def main(argv):

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument(
        "-i", "--input_file", help="The input file containing the fake data."
    )
    my_parser.add_argument(
        "-o",
        "--output_file",
        help="The output file to write the fake data, and the hardcoded data.",
    )

    args = my_parser.parse_args(argv[1:])

    input_file = args.input_file
    output_file = args.output_file

    # Check if the input and output files exists
    assert os.path.exists(input_file)

    # Retrieve the fake data from the input file
    fake_data = {}
    with open(input_file, "r") as f:
        fake_data = json.load(f)

    # Insert the hardcoded data in the fake data json
    for job_to_insert in get_jobs_hardcoded_values():
        fake_data["jobs"].append(job_to_insert)

    # Write the new fake data in the output file
    with open(output_file, "w") as f:
        json.dump(fake_data, f, indent=2)


if __name__ == "__main__":
    main(sys.argv)
