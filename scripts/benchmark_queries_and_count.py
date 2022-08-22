
# Script based on store_fake_data_in_db.py with the goal of benchmarking
# certain operations to compare their costs, and mostly to determine
# if it's reasonable to be running `count()` on MongoDB queries just
# to render the web front-end in more convenient way for the user.
# 
# https://mila-iqia.atlassian.net/browse/CW-154

# This script is meant to be run manually after running `bash dev.sh`
# and it doesn't use the web server at all.

# Open question: Should we modify some MongoDB index to facilitate
# searches for a given user? Right now we accelerate searches for
# pairs (job_id, cluster_name) but not for `fake_data["jobs"]["cw"]["mila_email_username"]`
# which could be a good idea.

# See the part of `populate_fake_data` in "fake_data.py" that does something like
#        db_insertion_point["jobs"].create_index(
#        [("cw.mila_email_username", 1), ("slurm.cluster_name", 1)],
#        name="mila_email_username_and_cluster_name",
#    )

import time
import json
import numpy as np
from test_common.fake_data import populate_fake_data
from clockwork_web.db import init_db, get_db
from clockwork_web.server_app import create_app
from tqdm import tqdm

def get_random_cluster_name(nbr_clusters):
    return "cluster_name_%d" % np.random.randint(low=0, high=nbr_clusters)

def get_random_mila_email_username(nbr_users):
    return "student_%d@mila.quebec" % np.random.randint(low=0, high=nbr_users)

def insert_more_fake_data(db, nbr_users=10, nbr_clusters=4):
    """
    Returns how many data points were inserted.
    """

    input_file = "/clockwork/test_common/fake_data.json"
    with open(input_file, "r") as infile:
        fake_data = json.load(infile)

    # print(f"number of data['jobs'] present: {len(fake_data['jobs'])}")

    for D_job in fake_data["jobs"]:
        # mutate the dict elements of the list
        D_job["slurm"]["cluster_name"] = get_random_cluster_name(nbr_clusters)
        D_job["cw"]["mila_email_username"] = get_random_mila_email_username(nbr_users)
        # let's just change job_id in case this messes up some index internally
        D_job["slurm"]["job_id"] = np.random.randint(low=0, high=1e9)

    # del fake_data["nodes"]
    # del fake_data["users"]

    # Write the data in a JSON file
    with open("/clockwork/test_common/tmp.json", "w") as outfile:
        json.dump(fake_data, outfile, indent=2)

    cf = populate_fake_data(db, json_file="/clockwork/test_common/tmp.json")
    return len(fake_data["jobs"]), cf


def run():

    nbr_users, nbr_clusters = (200, 4)
    # nbr_users, nbr_clusters = (2, 4)
    nbr_items_to_display = 100
    want_repopulate_db = True
    want_create_index = False # True
    want_create_index_str = "i" if want_create_index else ""
    total_database_size_target = 1e5
    total_database_size_target_str = "1e5"

    app = create_app(extra_config={"TESTING": True, "LOGIN_DISABLED": True})
    with app.app_context():
        init_db()
        db = get_db()

        if want_repopulate_db:

            # delete the whole thing to make sure we start from scratch if we run this
            # multiple times            
            db["jobs"].delete_many({})
            assert db["jobs"].count_documents({}) == 0

            total_inserted = 0

            # do once to estimate how much is inserted each time
            nbr_inserted, cf = insert_more_fake_data(db, nbr_users=nbr_users, nbr_clusters=nbr_clusters)
            T = int(total_database_size_target / nbr_inserted)+1
            for i in tqdm (range (1, T), desc="Inserting jobs in db..."):
                insert_more_fake_data(db, nbr_users=nbr_users, nbr_clusters=nbr_clusters)

            #while total_inserted <= total_database_size_target:
            #    nbr_inserted, cf = insert_more_fake_data(db, nbr_users=nbr_users, nbr_clusters=nbr_clusters)
            #    total_inserted += nbr_inserted
            #    print(f"total_inserted : {total_inserted}")

        total_inserted = db["jobs"].count_documents({})
        print(f"total number of documents in database : {total_inserted}")

        # this is a blocking operation so we'll have the index properly built
        # after we run this command
        start_timestamp = time.time()
        if want_create_index:
            db["jobs"].create_index(
                [("cw.mila_email_username", 1), ("slurm.cluster_name", 1)],
                name="mila_email_username_and_cluster_name",
            )
        index_building_duration = time.time() - start_timestamp
        print(f"building the index took {index_building_duration:.3f}s")

        # Note that if we were running the same request all the time, maybe some things
        # would get cached and it would run faster.

        LD_results = []

        total_expected_to_be_found = total_inserted / nbr_clusters / nbr_users

        for nbr_skipped_items in np.linspace(0, int(total_expected_to_be_found*1.5), 100):
            nbr_skipped_items = int(nbr_skipped_items)

            # Conceptually we could have done
            #     range(0, total_inserted, nbr_items_to_display)
            # or with `100*nbr_items_to_display` but we don't really need to test all values.
            # We just need a fair idea over the domain, with 100 measurements.

            mongodb_filter = {"$and": [
                {"slurm.cluster_name": get_random_cluster_name(nbr_clusters)},
                {"cw.mila_email_username": get_random_mila_email_username(nbr_users)},
                ]}

            start_timestamp = time.time()
            results = list(db["jobs"]
                .find(mongodb_filter)
                .skip(nbr_skipped_items)
                .limit(nbr_items_to_display)
            )
            single_page_duration = time.time() - start_timestamp

            start_timestamp = time.time()
            # https://www.mongodb.com/docs/manual/reference/method/db.collection.count/
            total_results_count = db["jobs"].count_documents(mongodb_filter)
            count_duration = time.time() - start_timestamp

            nbr_results_on_page = len(results)
            print(f"Skipping {nbr_skipped_items} takes {single_page_duration:0.3f}s, with {nbr_results_on_page} results on page. Total count takes {count_duration:0.3f}s.")

            LD_results.append(
                dict(   single_page_duration=single_page_duration,
                        nbr_skipped_items=nbr_skipped_items,
                        nbr_items_to_display=nbr_items_to_display,
                        total_inserted=total_inserted,
                        nbr_results_on_page=nbr_results_on_page,
                        count_duration=count_duration)
            )

    with open(f"/clockwork/scripts/benchmarks/queries_and_count_{nbr_users}_{nbr_clusters}_{total_database_size_target_str}{want_create_index_str}.json", "w") as f:
        json.dump(LD_results, f, indent=2)

if __name__ == "__main__":
    run()