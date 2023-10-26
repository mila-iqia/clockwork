# Imports to retrieve the values related to Slurm command
from slurm_state.helpers.ssh_helper import launch_slurm_command, open_connection
from slurm_state.helpers.clusters_helper import get_all_clusters

# Common imports
import os


class SlurmParser:
    """
    A parser for Slurm entities
    """

    def __init__(self, entity, slurm_command, cluster_name):
        self.entity = entity
        assert entity in ["jobs", "nodes"]

        self.cluster = get_all_clusters()[cluster_name]
        self.cluster["name"] = cluster_name

        self.slurm_command = slurm_command
        # Retrieve the path to the Slurm command we want to launch on the cluster
        # It is stored in the cluster data under the key "sacct_path" for the sacct command
        # and "sinfo_path" for the sinfo command
        self.slurm_command_path = self.cluster[f"{self.slurm_command}_path"]
        # Check if slurm_command_path exists
        assert (
            self.slurm_command_path
        ), f"Error. We have called the function to make updates with {self.slurm_command} but the {self.slurm_command}_path config is empty."
        assert self.slurm_command_path.endswith(
            self.slurm_command
        ), f"Error. The {self.slurm_command}_path configuration needs to end with '{self.slurm_command}'. It is currently {self.slurm_command_path} ."

        # Retrieve the version of Slurm installed on the current cluster
        self.slurm_version = self.get_slurm_version()

    def get_slurm_version(self):
        """
        Get the Slurm version
        """
        # Launch the sacct or sinfo command to get its version
        remote_command = f"{self.slurm_command_path} -V"
        response = self.launch_slurm_command(remote_command)
        assert len(response) == 1
        return response[0]

    def launch_slurm_command(self, remote_command):
        """ """
        return launch_slurm_command(
            remote_command,
            self.cluster["remote_hostname"],
            self.cluster["remote_user"],
            self.cluster["ssh_key_filename"],
            self.cluster["ssh_port"],
        )

    def generate_report(self, remote_command, file_name):
        """
        Launch a Slurm command in order to retrieve JSON report containing
        jobs or nodes information

        Parameters:
            cluster_name        The name of the cluster on which the Slurm command will be launched
            remote_command      The command used to retrieve the data from Slurm
            file_name           The path of the report file to write
        """
        # Launch the requested command in order to retrieve Slurm information
        stdout = self.launch_slurm_command(remote_command)

        # Create directories if needed
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        # Write the command output to a file
        with open(file_name, "w") as outfile:
            for line in stdout:
                outfile.write(line)
