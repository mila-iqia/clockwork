"""
We have a setup that scrapes data and writes it in a local database (also prometheus and elasticsearch).

We want to perform updates to the entries in a remote database (i.e. on Mongodb's Atlas service)
based on the entries recently scraped. We will only update the most recent entries
because the web interface will only list entries going one week in the past (by design, to
avoid huge queries).

We need to provide this script with arguments for source and destination.

As an extra feature, we can also run a query that will delete the oldest entries
in the destination database.

There are going to be some mentions of "one week" in this script,
but keep in mind that this timespan is arbitrary, and we can revise our choice later.

In the particular case of Clockwork Cluster, we want to update all the nodes all the time,
but we only want to update the most recent jobs. Updating "users" doesn't make any sense.
This means that the calls to this script should be mindful of specifying a `days_to_expire`
argument only when dealing with the "jobs" collection.

TODO : There's probably a reason to clean up the entries in the "nodes" collection from time
       to time, because nodes that get decommissioned shouldn't stay in the database forever.
       If we totally wiped "nodes" all the time, before updating them, this might be a little
       drastic because users might make queries from the web site that see an empty database.
       That wouldn't be a good thing.

       Maybe the solution is to write a separate script for "jobs" and "nodes" collections
       since the rules are somewhat different.
"""

import time

import argparse
from pymongo import MongoClient

parser = argparse.ArgumentParser(description='Migrate data from one instance of mongodb to another.')
parser.add_argument('--src_host', type=str,
                    help='source mongodb connection string')
parser.add_argument('--dst_host', type=str,
                    help='destination mongodb connection string')
parser.add_argument('--src_db', type=str, default="clockwork",
                    help='source mongodb database')
parser.add_argument('--dst_db', type=str, default="clockwork",
                    help='destination mongodb database')
parser.add_argument('--coll', type=str, default="jobs",
                    help='collection to transfer')
parser.add_argument('--days_to_expiration', type=int, default=None, # default is to not apply filtering
                    help='how many days before we ignore the source data (and purge from destination)')

args = parser.parse_args()

def main(src_host:str, src_db:str,
         dst_host:str, dst_db:str,
         coll:str,
         days_to_expiration):

    src = MongoClient(src_host)[src_db]
    dst = MongoClient(dst_host)[dst_db]

    if days_to_expiration is None:
        mongodb_src_filter_for_update = {}
        # We might as well cause an interpreter error here,
        # by omitting to define `mongodb_filter_for_removal`.
        # We never want to reach code that requires
        # the variable `mongodb_filter_for_removal` when
        # `days_to_expiration` is None.
        # mongodb_filter_for_removal = None
    else:
        seconds_to_expiration = days_to_expiration*3600*24
        # Those jobs; you want to update.
        mongodb_src_filter_for_update = {
            '$or' : [   {'end_time': {'$gt': int(time.time() - seconds_to_expiration)}},
                        {'end_time': 0}]
            }
        # Those jobs; you want to remove them.
        # At least remove them from the destination,
        # but maybe we'd want to remove them from the
        # source as well. TBD.
        # This filter is pretty much the negation of the
        # previous filter.
        mongodb_filter_for_removal = {
            '$and' : [  {'end_time': {'$lt': int(time.time() - seconds_to_expiration)}},
                        {'end_time': {'$ne': 0}}]
            }

    # Query is on SOURCE.
    nbr_updated = 0
    for e in src[coll].find(mongodb_src_filter_for_update):
        # Perform the updates by mongodb '_id' field so we
        # don't have to know anything about the particular
        # meaning of the data contained.
        dst[coll].update_one({'_id': e['_id']}, {"$set": e}, upsert=True)
        nbr_updated += 1
    print(f"Updated {nbr_updated} from collection {coll} in destination.")


    # Hardcoding a certain protection.
    # This is a sign that the tool wasn't designed as something elegant and general,
    # but it's to prevent accidents.
    if coll == "jobs" and days_to_expiration is not None:
        # Query is on DESTINATION.
        nbr_deleted = dst[coll].delete_many(mongodb_filter_for_removal)
        print(f"Deleted {nbr_deleted} from collection {coll} in destination.")
        # No need to do it for individual entries.
        # for e in dst[coll].find(mongodb_filter_for_removal):
        #     dst[coll].delete_one({'_id': e['_id']})


if __name__ == "__main__":

    main(   src_host=args.src_host,
            src_db=args.src_db,
            dst_host=args.dst_host,
            dst_db=args.dst_db,
            coll=args.coll.replace(" ", ""),
            days_to_expiration=args.days_to_expiration)
