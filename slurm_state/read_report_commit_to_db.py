"""
This script is to be called from cron on `blink`, or wherever the "slurm reports"
are found on the local filesystem.

It serves as the entry point to the code in "mongo_update.py" that
does the actual work, and calls "sacct_parser.py" and "sinfo_parser.py" internally.

The parameters of this function are exposed through command-line arguments
because of the particular setup in which this script is going to be used.
It is not going to run inside a Docker container.

It expects that a MongoDB database is online, accessible, and that it can
connect to it through a simple connection string given as command-line argument.
"""

import os
import argparse
from slurm_state.mongo_client import get_mongo_client
from slurm_state.mongo_update import main_read_report_and_update_collection


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Parse slurm report files and load them to a database.",
    )

    parser.add_argument(
        "--slurm_jobs_file",
        help="The Slurm jobs file. Could be used as an input file if the option --from_existing_jobs_file is given. Otherwise, this file is generated from a sacct command.",
    )

    parser.add_argument(
        "--cw_jobs_file",
        required=False,
        help="Path to dump the Clockwork jobs. If None, no Clockwork jobs file is written.",
    )

    parser.add_argument(
        "--from_existing_jobs_file",
        action=argparse.BooleanOptionalAction,
        help="Whether or not the jobs are retrieved from a file instead of a sacct command.",
    )

    parser.add_argument(
        "--slurm_nodes_file",
        required=False,
        help="The Slurm nodes file. Could be used as an input file if the option --from_existing_nodes_file is given. Otherwise, this file is generated from a sinfo command.",
    )

    parser.add_argument(
        "--cw_nodes_file",
        help="Path to dump the Clockwork nodes. If None, no Clockwork nodes file is written.",
    )

    parser.add_argument(
        "--from_existing_nodes_file",
        action=argparse.BooleanOptionalAction,
        help="Whether or not the nodes are retrieved from a file instead of a sinfo command.",
    )

    parser.add_argument(
        "-c",
        "--cluster_name",
        required=True,
        help="Name of the cluster that produced the file",
    )

    parser.add_argument(
        "--store_in_db",
        action=argparse.BooleanOptionalAction,
        help="Whether or not the jobs and nodes are stored in db.",
    )

    parser.add_argument(
        "--mongodb_collection", default="clockwork", help="Collection to populate."
    )

    # Retrieve the args
    args = parser.parse_args(argv[1:])
    collection_name = args.mongodb_collection

    # Get the database instance
    client = get_mongo_client()

    #
    #   Parse the jobs
    #
    jobs_collection = client[collection_name]["jobs"]

    # https://stackoverflow.com/questions/33541290/how-can-i-create-an-index-with-pymongo
    # Apparently "ensure_index" is deprecated, and we should always call "create_index".
    if args.store_in_db:
        jobs_collection.create_index(
            [("slurm.job_id", 1), ("slurm.cluster_name", 1)],
            name="job_id_and_cluster_name",
        )

    main_read_report_and_update_collection(
        "jobs",
        jobs_collection,
        client[collection_name]["users"],
        args.cluster_name,
        args.slurm_jobs_file,
        from_file=args.from_existing_jobs_file,
        want_commit_to_db=args.store_in_db,
        dump_file=args.cw_jobs_file,
    )

    #
    #   Parse the nodes
    #
    """
    # Ignore the "nodes" part for now

    nodes_collection = client[collection_name]["nodes"]

    if args.store_in_db:
        nodes_collection.create_index(
            [("slurm.name", 1), ("slurm.cluster_name", 1)],
            name="name_and_cluster_name",
        )

    main_read_report_and_update_collection(
        "nodes",
        nodes_collection,
        None,
        args.cluster_name,
        args.slurm_nodes_file,
        from_file=args.from_existing_nodes_file,
        want_commit_to_db=args.store_in_db,
        dump_file=args.cw_nodes_file,
    )
    """


if __name__ == "__main__":
    import sys

    main(sys.argv)

"""
export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_passowrd_okay"
export MONGODB_CONNECTION_STRING="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@127.0.0.1:37017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false"
export MONGODB_DATABASE_NAME="clockwork"
export slurm_state_ALLOCATIONS_RELATED_TO_MILA="./allocations_related_to_mila.json"

python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --jobs_file ../tmp/slurm_report/beluga/sacct_job \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --nodes_file ../tmp/slurm_report/beluga/sacct_node \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

# dump file only
python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --jobs_file ../tmp/slurm_report/beluga/sacct_job \
    --dump_file ../tmp/slurm_report/beluga/job_dump_file.json

# This would out empty due to fake allocations if you don't
# specify a different allocation file.
export slurm_state_ALLOCATIONS_RELATED_TO_MILA="../slurm_state_test/fake_allocations_related_to_mila.json"
python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --jobs_file ../tmp/slurm_report/beluga/sacct_job_anonymized \
    --dump_file ../tmp/slurm_report/beluga/job_dump_file_anonymized.json

python3 read_report_commit_to_db.py \
    --cluster_name mila \
    --jobs_file ../tmp/slurm_report/mila/sacctjob \
    --dump_file dump_file_mila.json

"""
