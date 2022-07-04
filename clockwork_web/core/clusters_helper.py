"""
Helper function regarding the clusters.
"""


def get_account_fields():
    """
    Retrieve the keys identifying the account for each cluster. Follows an
    example of the returned dictionary:
    {
        "cc_account_username": ["beluga", "cedar", "graham", "narval"],
        "mila_cluster_username": ["mila"],
        "test_cluster_username": ["test_cluster"]
    }
    """
    # Retrieve the information on the clusters
    D_all_clusters = get_all_clusters()

    # Initialize the dictionary of account fields
    D_account_fields = {}

    for cluster_name in D_all_clusters.keys():
        # For each cluster, get the name of the account field
        account_field = D_all_clusters[cluster_name]["account_field"]

        if account_field in D_account_fields:
            # If the account field is know in D_account_fields, add the name of the
            # cluster in the associated clusters array
            D_account_fields[account_field].append(cluster_name)

        else:
            # Otherwise, associate a list containing the current cluster's name
            # to the account field
            D_account_fields[account_field] = [cluster_name]

    # Return the dictionary presenting the different account fields and their
    # associated clusters
    return D_account_fields
