# These functions are translators used in order to handle the values
# we could encounter while parsing a job dictionary retrieved from a
# sacct command.
from slurm_state.helpers.parser_helper import (
    copy,
    copy_and_stringify,
    extract_tres_data,
    join_subitems,
    rename,
    rename_subitems,
    rename_and_stringify_subitems,
    translate_with_value_modification,
    zero_to_null,
)

from slurm_state.parsers.slurm_parser import SlurmParser

# Common imports
import json, re


class JobParser(SlurmParser):
    """ """

    def __init__(self, cluster_name):
        super().__init__("jobs", "sacct", cluster_name)

    def generate_report(self, file_name):

        # Retrieve the allocations associated to the cluster
        allocations = self.cluster["allocations"]

        if allocations == []:
            # If the cluster has no associated allocation, nothing is requested
            print(
                f"The cluster {self.cluster['name']} has no allocation related to it. Thus, no job has been retrieved. Associated allocations can be provided in the Clockwork configuration file."
            )
            return []
        else:
            # Set the sacct command
            # -S is a condition on the start time, 600 being in seconds
            # -E is a condition on the end time
            # -X means "Only show statistics relevant to the job allocation itself, not taking steps into consideration."
            # --associations is used in order to limit the fetched jobs to the ones related to Mila and/or professors who
            #                may use Clockwork
            if allocations == "*":
                # We do not provide --associations information because the default for this parameter
                # is "all associations"
                remote_command = (
                    f"{self.slurm_command_path} -S now-600 -E now -X --allusers --json"
                )
            else:
                accounts_list = ",".join(allocations)
                remote_command = f"{self.slurm_command_path} -S now-600 -E now -X --accounts={accounts_list} --allusers --json"
            print(f"remote_command is\n{remote_command}")

        return super().generate_report(remote_command, file_name)

    def parser(self, f):
        """ """
        if re.search("^slurm 22\..*$", self.slurm_version):
            return self.parser_v22_and_23(f)
        elif re.search("^slurm 23\..*$", self.slurm_version):
            return self.parser_v22_and_23(f)
        else:
            raise Exception(
                f'The {self.entity} parser is not implemented for the Slurm version "{self.slurm_version}".'
            )

    def parser_v22_and_23(self, f):
        JOB_FIELD_MAP = {
            "account": copy,
            "array": rename_and_stringify_subitems(
                {"job_id": "array_job_id", "task_id": "array_task_id"}
            ),
            "cluster": rename("cluster_name"),
            "exit_code": join_subitems(":", "exit_code"),
            "job_id": copy_and_stringify,
            "name": copy,
            "nodes": copy,
            "partition": copy,
            "state": rename_subitems({"current": "job_state"}),
            "time": translate_with_value_modification(
                zero_to_null,
                rename_subitems,
                subitem_dict={
                    "limit": "time_limit",
                    "submission": "submit_time",
                    "start": "start_time",
                    "end": "end_time",
                },
            ),
            "tres": extract_tres_data,
            "user": rename("username"),
            "working_directory": copy,
        }

        # Load the JSON file generated using the Slurm command
        # (At this point, slurm_data is a hierarchical structure of dictionaries and lists)
        slurm_data = json.load(f)

        slurm_entities = slurm_data[self.entity]

        for slurm_entity in slurm_entities:
            res_entity = (
                dict()
            )  # Initialize the dictionary which will store the newly formatted Slurm data

            for k, v in slurm_entity.items():
                # We will use a handler mapping to translate this
                translator = JOB_FIELD_MAP.get(k, None)

                if translator is not None:
                    # Translate using the translator retrieved from the fields map
                    translator(k, v, res_entity)

                # If no translator has been provided: ignore the field

            yield res_entity
