import json

with open("node.json", "r") as f:
    nodes_data = json.load(f)

L_partitions = []
for (k, node_data) in nodes_data.items():
    L_partitions.extend(node_data["partitions"])

print(list(set(L_partitions)))