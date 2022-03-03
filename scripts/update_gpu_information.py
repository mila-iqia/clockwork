"""
Update the GPU information in the 'hardware' collection of the database.

This script uses a JSON file as input, presenting the known information
about the GPU.
"""

import argparse
import json
import sys
import pymongo

from slurm_state.mongo_client import get_mongo_client


def main(argv):

    # Retrieve the GPU information
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--json_input", type=argparse.FileType("r"), help="JSON file containing"
    )
    parser.add_argument(
        "--mongodb_connection_string", help="Connection string used by MongoClient"
    )

    parser.add_argument(
        "--mongodb_database_name", help="Name of the database we want to access to"
    )

    args = parser.parse_args(argv[1:])

    # Variables initialization
    gpu_infos = json.load(args.json_input)
    mongodb_connection_string = args.mongodb_connection_string
    mongodb_database_name = args.mongodb_database_name

    # Connect to the database
    hardware_collection = get_mongo_client(mongodb_connection_string)[
        mongodb_database_name
    ]["hardware"]

    # Update or insert the gpu information
    for gpu_info in gpu_infos["gpu_infos"]:
        try:
            hardware_collection.update_one(
                # Rule to match if already present in collection
                {
                    "name": gpu_info["name"],
                },
                # The data to write in the collection
                {
                    "$set": gpu_info,
                },
                # Create if missing, update if present
                upsert=True,
            )
        except Exception as e:
            print(f"An error occurred while inserting the GPU: {gpu_info['name']}")
            print(e)


if __name__ == "__main__":
    main(sys.argv)
