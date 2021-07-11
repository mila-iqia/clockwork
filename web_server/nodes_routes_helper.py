
from mongo_client import get_mongo_client

def get_nodes(find_filter:dict={}):
    mc = get_mongo_client()
    mc_db = mc['slurm']
    return list(mc_db["nodes"].find(find_filter))


def strip_artificial_fields_from_node(D_node):
    # Returns a copy. Does not mutate the original.
    fields_to_remove = ["_id", "grafana_helpers"]
    return dict( (k, v) for (k, v) in D_node.items() if k not in fields_to_remove)