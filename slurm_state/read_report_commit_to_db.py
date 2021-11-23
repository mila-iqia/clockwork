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
from mongo_client import get_mongo_client
from mongo_update import (
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
        "--cluster_desc",
        required=True,
        help="Path to a cluster description file (json format).",
    )

    parser.add_argument(
        "--mongodb_connection_string", help="Connection string used by MongoClient."
    )
    parser.add_argument(
        "--mongodb_collection", default="clockwork", help="Collection to populate."
    )

    parser.add_argument(
        "--dump_file",
        help="Dump the data to the specified file, used for debugging. Can work even without an instance of MongoDB running.",
    )

    args = parser.parse_args(argv[1:])
    print(args)

    connection_string = args.mongodb_connection_string
    collection_name = args.mongodb_collection

    if not connection_string or not collection_name:
        # We will only write out the results to `args.dump_file` in this case.
        assert (
            args.dump_file
        ), f"Error. Given that mongodb_connection_string ({args.mongodb_connection_string}) or mongodb_collection ({args.mongodb_collection}) are missing, we can still write the results to a the 'dump_file' argument. However, right now this argument is also missing, so we can't do anything."
        want_commit_to_db = False
        client = None
    else:
        want_commit_to_db = True
        client = get_mongo_client(connection_string)

    if args.jobs_file:
        assert os.path.exists(args.jobs_file)
        assert os.path.exists(args.cluster_desc)
        main_read_jobs_and_update_collection(
            client[collection_name]["jobs"] if client else None,
            args.cluster_desc,
            args.jobs_file,
            want_commit_to_db=want_commit_to_db,
            dump_file=args.dump_file,
        )

    if args.nodes_file:
        assert os.path.exists(args.nodes_file)
        assert os.path.exists(args.cluster_desc)
        main_read_nodes_and_update_collection(
            client[collection_name]["nodes"] if client else None,
            args.cluster_desc,
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
    --cluster_desc cluster_desc/beluga.json \
    --jobs_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

python3 read_report_commit_to_db.py \
    --cluster_desc cluster_desc/beluga.json \
    --nodes_file ../tmp/slurm_report/beluga/scontrol_show_node \
    --mongodb_connection_string ${MONGODB_CONNECTION_STRING} \
    --mongodb_collection ${MONGODB_DATABASE_NAME}

# dump file only
python3 read_report_commit_to_db.py \
    --cluster_desc cluster_desc/beluga.json \
    --jobs_file ../tmp/slurm_report/beluga/scontrol_show_job \
    --dump_file dump_file_beluga.json

python3 read_report_commit_to_db.py \
    --cluster_desc cluster_desc/mila.json \
    --jobs_file ../tmp/slurm_report/mila/scontrol_show_job \
    --dump_file dump_file_mila.json

"""
