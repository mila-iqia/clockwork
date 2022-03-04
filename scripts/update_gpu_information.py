"""
Update the GPU information in the 'hardware' collection of the database.

This script uses a JSON file as input, presenting the known information
about the GPU.
"""

import argparse
import json
import sys
from pymongo import MongoClient


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

    update_gpu_information(gpu_infos, mongodb_connection_string, mongodb_database_name)

def update_gpu_information(gpu_infos, mongodb_connection_string, mongodb_database_name, mongodb_collection_name="hardware"):
    """
    Update the GPU information in the 'hardware' collection of the database.

    Parameters:
        gpu_infos: JSON dictionary containing the GPU informations to insert
            or update. It format is the following:
            {
                "gpu_infos": <list of dictionaries presenting each a GPU>
            }
    """
    # Connect to the database
    hardware_collection = MongoClient(mongodb_connection_string)[
        mongodb_database_name
    ][mongodb_collection_name]

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
