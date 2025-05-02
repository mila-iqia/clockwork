# Imports to retrieve the values related to Slurm command
from slurm_state.helpers.ssh_helper import launch_slurm_command, open_connection
from slurm_state.helpers.clusters_helper import get_all_clusters

# Common imports
import json, os, re


class EntityParser:
    """
    A parser for Slurm entities
    """

    def __init__(self, entity, cluster_name, slurm_command=None, slurm_version=None):
        self.entity = entity
        assert entity in ["jobs", "nodes"]

        self.cluster = get_all_clusters()[cluster_name]
        self.cluster["name"] = cluster_name

        # Get the Slurm version associated to the cluster
        if slurm_version is not None:
            self.slurm_version = slurm_version
        elif (
            "slurm_version" in self.cluster
            and self.cluster["slurm_version"] is not None
        ):
            self.slurm_version = self.cluster["slurm_version"]
        else:
            # If no Slurm version is provided, whether by configuration file nor parameters,
            # raise an error
            raise Exception(
                f"No Slurm version has been identified fo the {self.cluster['name']} cluster. Please provide it through the configuration file or the command parameters."
            )


class IdentityParser(EntityParser):
    def __init__(self, entity, cluster_name):
        self.entity = entity

        self.cluster = get_all_clusters()[cluster_name]
        self.cluster["name"] = cluster_name

    def parser(self, f):
        # Load the JSON file generated using the Slurm command
        # (At this point, slurm_data is a hierarchical structure of dictionaries and lists)
        entities = json.load(f)
        for entity in entities:
            if entity["slurm"]["cluster_name"] == self.cluster["name"]:
                yield entity
