"""
This script is to be called from cron on `blink`, or wherever the "slurm reports"
are found on the local filesystem.

It serves as the entry point to the code in "mongo_update.py" that
does the actual work, and calls "scontrol_parser.py" internally.

The parameters of this function are exposed through command-line arguments
because of the particular setup in which this script is going to be used.
It is not going to run inside a Docker container.

It expects that a MongoDB database is online, accessible, and that it can
connect to it through a simple connection string given as command-line argument.
"""

import os
import argparse
from slurm_state.mongo_client import get_mongo_client
from slurm_state.mongo_update import (
    main_read_nodes_and_update_collection,
    main_read_jobs_and_update_collection,
)


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Parse slurm report files and load them to a database.",
    )

    parser.add_argument("-j", "--jobs_file", help="The jobs file.")
    parser.add_argument("-n", "--nodes_file", help="The nodes file.")
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

    parser.add_argument(
        "--dump_file",
        help="Dump the data to the specified file, used for debugging. Can work even without an instance of MongoDB running.",
    )

    # Retrieve the args
    args = parser.parse_args(argv[1:])
    collection_name = args.mongodb_collection

    # Get the database instance
    client = get_mongo_client()
    if not args.store_in_db:
        # We will only write out the results to `args.dump_file` in this case.
        assert (
            args.dump_file
        ), f"Error. Given that the results are not written in the database, we can still write the results to a the 'dump_file' argument. However, right now this argument is also missing, so we can't do anything."
        want_commit_to_db = False
    else:
        # We will both write out the results in the `args.dump_file` and in the
        # database
        want_commit_to_db = True

    if args.jobs_file:
        assert os.path.exists(args.jobs_file)
        jobs_collection = client[collection_name]["jobs"]

        # https://stackoverflow.com/questions/33541290/how-can-i-create-an-index-with-pymongo
        # Apparently "ensure_index" is deprecated, and we should always call "create_index".
        if want_commit_to_db:
            jobs_collection.create_index(
                [("slurm.job_id", 1), ("slurm.cluster_name", 1)],
                name="job_id_and_cluster_name",
            )

        main_read_jobs_and_update_collection(
            jobs_collection,
            client[collection_name]["users"],
            args.cluster_name,
            args.jobs_file,
            want_commit_to_db=want_commit_to_db,
            want_sacct=False, # as we already have an input file
            dump_file=args.dump_file,
        )

    if args.nodes_file:
        assert os.path.exists(args.nodes_file)
        nodes_collection = client[collection_name]["nodes"]

        if want_commit_to_db:
            nodes_collection.create_index(
                [("slurm.name", 1), ("slurm.cluster_name", 1)],
                name="name_and_cluster_name",
            )
        main_read_nodes_and_update_collection(
            nodes_collection,
            args.cluster_name,
            args.nodes_file,
            want_commit_to_db=want_commit_to_db,
            dump_file=args.dump_file,
        )


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
    --jobs_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --nodes_file ../tmp/slurm_report/beluga/scontrol_show_node \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

# dump file only
python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --jobs_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --dump_file ../tmp/slurm_report/beluga/job_dump_file.json

# This would out empty due to fake allocations if you don't
# specify a different allocation file.
export slurm_state_ALLOCATIONS_RELATED_TO_MILA="../slurm_state_test/fake_allocations_related_to_mila.json"
python3 read_report_commit_to_db.py \
    --cluster_name beluga \
    --jobs_file ../tmp/slurm_report/beluga/scontrol_show_job_anonymized \
    --dump_file ../tmp/slurm_report/beluga/job_dump_file_anonymized.json

python3 read_report_commit_to_db.py \
    --cluster_name mila \
    --jobs_file ../tmp/slurm_report/mila/scontrol_show_job \
    --dump_file dump_file_mila.json

"""
