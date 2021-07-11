"""
This little script is just a way to list the partitions from each of the clusters
to be able to fill out the configuration needed by mini_sinfo_01.py.

In a way, there's a little chicken-and-egg thing going on, because you probably
want to run mini_sinfo_01.py at first without knowing anything about the partitions.
This just means that the Prometheus counters exposed won't have information about
those partitions, which is totally okay.

This script doesn't use pyslurm to get any information, but it simply reads the
database in mongodb to see what information has been populated previously through
a call to `pyslurm.node().get()`. This is clumsy.
"""


from mongo_client import get_mongo_client
from collections import defaultdict

def main():
    mc = get_mongo_client({"hostname":"deepgroove.local", "port":27017, "username":"mongoadmin", "password":"secret_password_okay"})
    print(mc['slurm'].list_collection_names())


    D_cluster_name_to_partitions = defaultdict(set)
    for e in mc['slurm']['nodes'].find():
        for partition_name in e.get('partitions', []):
            D_cluster_name_to_partitions[e['cluster_name']].add(partition_name)

    for cluster_name, S_partition_names in D_cluster_name_to_partitions.items():

        print(f"""


==================
    {cluster_name}
==================
""")
        print(list(S_partition_names))

if __name__ == "__main__":
    main()