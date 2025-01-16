"""
Some tests require hardcoded values in the resulting fake data. Thus, this
script is used to insert them in the JSON containing the fake data.
"""

import argparse
import json
import os
import sys
import random


def get_jobs_hardcoded_values():
    """
    Returns the hardcoded data to be inserted in the jobs list of the fake data.
    """
    return [
        {
            "slurm": {
                "job_id": "284357",
                "array_job_id": "0",
                "array_task_id": "None",
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
        }
    ]


def get_job_user_props_hardcoded_values(fake_data: dict):
    """
    Return partially hardcoded data to be inserted as fake job user props.

    This function will generate 5 job user props
    associated to the 5 first jobs from fake data
    edited by 2nd user available in fake data (i.e. `student01`)
    """
    mila_email_username = fake_data["users"][1]["mila_email_username"]
    jobs = fake_data["jobs"][:5]
    user_props = [
        {"name": "je suis une user prop 1"},
        {"name": "je suis une user prop 2"},
        {"name": "je suis une user prop 3"},
        {"name": "je suis une user prop 3", "name2": "je suis une user prop 4"},
        {
            "comet_hyperlink": "https://comet.example.com",
            "wandb_hyperlink": "https://wandb.example.com/?job=thisjob",
        },
    ]

    return [
        {
            "mila_email_username": mila_email_username,
            "job_id": job["slurm"]["job_id"],
            "cluster_name": job["slurm"]["cluster_name"],
            "props": props,
        }
        for job, props in zip(jobs, user_props)
    ]


def ensure_admin_users(fake_data: dict):
    """Make sure there is at least 1 fake admin."""
    users = fake_data["users"]
    admin_users = [user for user in users if user.get("admin_access", False)]
    if not admin_users and users:
        users[0]["admin_access"] = True
        assert [user for user in fake_data["users"] if user.get("admin_access", False)]


def ensure_job_arrays(fake_data: dict):
    """Make sure some fake jobs belong to valid job arrays."""
    jobs_with_array_id = [
        job for job in fake_data["jobs"] if job["slurm"]["array_job_id"] != "0"
    ]
    if not jobs_with_array_id:
        # No yet jobs in valid job arrays.
        # Add 2 jobs to 2 separate job arrays.
        nb_fake_jobs = len(fake_data["jobs"])
        assert nb_fake_jobs >= 2
        id_job_1 = random.randint(0, nb_fake_jobs)
        id_job_2 = (id_job_1 + 1) % nb_fake_jobs
        fake_data["jobs"][id_job_1]["slurm"]["array_job_id"] = "1234"
        fake_data["jobs"][id_job_2]["slurm"]["array_job_id"] = "5678"

    assert [job for job in fake_data["jobs"] if job["slurm"]["array_job_id"] != "0"]


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
    assert os.path.exists(output_file)

    # Retrieve the fake data from the input file
    fake_data = {}
    with open(input_file, "r") as f:
        fake_data = json.load(f)

    # Insert the hardcoded data in the fake data json
    for job_to_insert in get_jobs_hardcoded_values():
        fake_data["jobs"].append(job_to_insert)

    # Insert fake job user props
    fake_data["job_user_props"] = get_job_user_props_hardcoded_values(fake_data)

    # Make sure there are some admin users
    ensure_admin_users(fake_data)

    # Make sure some jobs are in valid job arrays
    ensure_job_arrays(fake_data)

    # Write the new fake data in the output file
    with open(output_file, "w") as f:
        json.dump(fake_data, f, indent=2)


if __name__ == "__main__":
    main(sys.argv)
