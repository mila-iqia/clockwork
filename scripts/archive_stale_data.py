"""
Takes all the data from the "jobs" and "nodes" collection and retrieves
everything that hasn't been updated for a month (or some other timestamp).

We refer to the field e["cw]["last_slurm_update"] to know
if some element e was updated recently or not.

If a JSON output file is specified, we will store the results in that file.
"""

import os
import sys
import argparse
import time
from pprint import pprint
import json

from pymongo import DeleteOne
from pymongo.errors import BulkWriteError

from slurm_state.mongo_client import get_mongo_client



def main(argv):
    # Retrieve the args
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Removes the old data in Clockwork database and archives it somewhere else.",
    )

    parser.add_argument(
        "-u",
        "--archive_path",
        help="Optional. JSON file where we will put the elements removed.",
    )

    parser.add_argument(
        "--database_name", default="clockwork", help="Database name to inspect."
    )

    parser.add_argument(
        "--days_since_last_update", default=30, help="How many days since last update."
    )

    args = parser.parse_args(argv[1:])
    assert isinstance(args.days_since_last_update, int)

    archive(args.archive_path, args.database_name, args.days_since_last_update)


def archive(archive_path, database_name, days_since_last_update):

    threshold_timestamp = time.time() - days_since_last_update * 24 * 60 * 60

    # Okay, so here's a minor problem.
    # We don't want to leave out certain jobs by running the same query twice
    # but with the filter catching different jobs due to time moving on.
    #
    # We also don't want to remove jobs before we archive them.
    # We'll run a bulk update with the unique ids, then, even though
    # that will be slower than just a `delete_many` call with a filter.
    # That way, we won't get duplicates in the archives, unless some deletion
    # operation fails, in which case we'll have archived something that stuck
    # around in the database.

    # Open the database and insert the users
    client = get_mongo_client()

    
    ###################
    ## Retrieve jobs ##
    ###################
    jobs_collection = client[database_name]["jobs"]
    LD_jobs_to_archive = list(jobs_collection.find({"cw.last_slurm_update": {"$lt": threshold_timestamp}}))

    # We don't want to store those "_id",
    # but we need them later to make a deletion operation.   
    L_jobs_deletion_requests = [DeleteOne({'_id': D_job["_id"]}) for D_job in LD_jobs_to_archive]
    for D_job in LD_jobs_to_archive:
        del D_job["_id"]


    ####################
    ## Retrieve nodes ##
    ####################
    nodes_collection = client[database_name]["nodes"]
    LD_nodes_to_archive = list(nodes_collection.find({"cw.last_slurm_update": {"$lt": threshold_timestamp}}))
    
    L_nodes_deletion_requests = [DeleteOne({'_id': D_node["_id"]}) for D_job in LD_nodes_to_archive]
    for D_node in LD_nodes_to_archive:
        del D_node["_id"]


    #############################
    ## Write things in archive ##
    #############################
    contents_archived = {"jobs": LD_jobs_to_archive, "nodes": LD_nodes_to_archive}
    if (archive_path and
        os.path.exists(os.path.dirname(archive_path))):
        with open(archive_path, "w") as f:
            json.dump(contents_archived, f, indent=2)


    #################################
    ## Deletions from the database ##
    #################################
    try:
        jobs_collection.bulk_write(L_jobs_deletion_requests, ordered=False)
    except BulkWriteError as bwe:
        pprint(bwe.details)

    try:
        nodes_collection.bulk_write(L_nodes_deletion_requests, ordered=False)
    except BulkWriteError as bwe:
        pprint(bwe.details)

    # Might as well return it. It also helps with testing this method.
    return contents_archived


if __name__ == "__main__":
    main(sys.argv)
