"""
For fun, with our database, can be associate the "user_id" to our best guesses as to the identity
of the people running the jobs?

This is more of a sanity check, and good fun, than out of necessity.
If it were a necessicity, we'd better find a more authoritative source of truth.
"""

from mongo_client import get_mongo_client
from collections import defaultdict
import json

def main():
    mc = get_mongo_client({"hostname":"deepgroove.local", "port":27017, "username":"mongoadmin", "password":"secret_password_okay"})

    user_id_to_mila_user_account = defaultdict(set)
    for e in mc['slurm']['jobs'].find():
        user_id_to_mila_user_account[ e['user_id'] ].add( (e['mila_user_account'], e['cluster_name']) )

    # convert from int->set to int->list
    user_id_to_mila_user_account = dict( (k, list(S)) for (k, S) in user_id_to_mila_user_account.items())

    # count the number of user_id for which there was only one associated mila_user_account
    unique_matches = len(list(1 for L in user_id_to_mila_user_account.values() if len(L) == 1))
    print(f"Out of {len(user_id_to_mila_user_account)} user_id, we have {unique_matches} with unique matches.")

    # D_single = {}
    for k, L in user_id_to_mila_user_account.items():
        if len(L) > 1:
            print(f"{k} maps to {L}")
        #else:
        #    D_single[k] = list(S)[0]
    
    # D_single[1500000098] = "fansitca"]
    with open("user_id_to_mila_user_account.json", "w") as f:
        json.dump(user_id_to_mila_user_account, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()