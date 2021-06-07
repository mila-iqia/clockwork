"""
This is just a script for convenience to read all the names of the accounts
that involved "bengio" on the Compute Canada machines.

Basically, the answer is ['def-bengioy_gpu', 'rrg-bengioy-ad_gpu', 'rrg-bengioy-ad_cpu', 'def-bengioy_cpu'].
No need to run this all the time once we have the answer.

"""

from mongo_client import get_mongo_client
import re

def main():
    mc = get_mongo_client({"hostname":"deepgroove.local", "port":27017, "username":"mongoadmin", "password":"secret_password_okay"})
    print(mc['slurm'].list_collection_names())


    S_accounts = set([])
    for e in mc['slurm']['jobs'].find():
        if re.match(r".*bengio.*", e['account']):
            S_accounts.add(e['account'])

    print(list(S_accounts))


if __name__ == "__main__":
    main()