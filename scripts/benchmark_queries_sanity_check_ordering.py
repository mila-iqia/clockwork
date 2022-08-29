"""
The purpose of this script is to test the hypothesis that "sort"
for MongoDB ACTUALLY DOES WHAT IT SAYS IT DOES, instead of simply
returning sorted pages without much consideration as to the
values between the pages.
E.g. (4,5,6), (1,2,3) is not a proper way to sort (1,2,3,4,5,6)
                      and list it in two pages

"""

import time
import json
import numpy as np
from test_common.fake_data import populate_fake_data
from clockwork_web.db import init_db, get_db
from clockwork_web.server_app import create_app
from tqdm import tqdm
import pymongo
from benchmark_queries_and_count import get_random_cluster_name, get_random_mila_email_username, insert_more_fake_data

def run():
    nbr_users, nbr_clusters = (10, 2)
    nbr_items_to_display = 10
    total_database_size_target = 1e4

    app = create_app(extra_config={"TESTING": True, "LOGIN_DISABLED": True})
    with app.app_context():
        init_db()
        db = get_db()

        nbr_inserted, cf = insert_more_fake_data(db, nbr_users=nbr_users, nbr_clusters=nbr_clusters)
        T = int(total_database_size_target / nbr_inserted)+1
        for i in tqdm (range (1, T), desc="Inserting jobs in db..."):
            insert_more_fake_data(db, nbr_users=nbr_users, nbr_clusters=nbr_clusters)


        mongodb_filter = {"$and": [
                {"slurm.cluster_name": get_random_cluster_name(nbr_clusters)},
                {"cw.mila_email_username": get_random_mila_email_username(nbr_users)},
                ]}

        print(mongodb_filter)
        total_results_count = db["jobs"].count_documents(mongodb_filter)
        print(f"total_results_count : {total_results_count}")

        L_results = []
        while True:
            nbr_skipped_items = len(L_results)
            results = list(db["jobs"]
                .find(mongodb_filter)
                .sort("slurm.submit_time", pymongo.ASCENDING)
                .skip(nbr_skipped_items)
                .limit(nbr_items_to_display)
            )
            if len(results) == 0:
                break
            else:
                L_results.extend(results)

    A = [e["slurm"]["submit_time"] for e in L_results]
    with open(f"/clockwork/scripts/benchmarks/debug.json", "w") as f:
        json.dump(A, f, indent=2)

    for (a, b) in zip(A[:-1], A[1:]):
        assert a <= b, (a, b)

if __name__ == "__main__":
    run()