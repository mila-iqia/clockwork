from slurm_state.parsers.entity_parser import EntityParser

# These functions are translators used in order to handle the values
# we could encounter while parsing a node dictionary retrieved from a
# sinfo command.
from slurm_state.helpers.parser_helper import (
    copy,
    copy_with_none_as_empty_string,
    rename,
)

# Common imports
import json, re


class NodeParser(EntityParser):
    """ """

    def __init__(self, cluster_name, slurm_version=None):
        super().__init__("nodes", cluster_name, "sinfo", slurm_version=slurm_version)

    def generate_report(self, file_name):
        # The command to be launched through SSH is "sinfo --json"
        remote_command = f"{self.slurm_command_path} --json"

        return super().generate_report(remote_command, file_name)

    def parser(self, f):
        """ """
        if re.search(r"^21\..*$", self.slurm_version):
            return self.parser_v21_and_v22(f)
        elif re.search(r"^22\..*$", self.slurm_version):
            return self.parser_v21_and_v22(f)
        else:
            raise Exception(
                f'The {self.entity} parser is not implemented for the Slurm version "{self.slurm_version}".'
            )

    def parser_v21_and_v22(self, f):
        NODE_FIELD_MAP = {
            "architecture": rename("arch"),
            "comment": copy,
            "cores": copy,
            "cpus": copy,
            "last_busy": copy,
            "features": copy,
            "gres": copy_with_none_as_empty_string,
            "gres_used": copy,
            "name": copy,
            "address": rename("addr"),
            "state": copy,
            "state_flags": copy,
            "real_memory": rename("memory"),
            "reason": copy,
            "reason_changed_at": copy,
            "tres": copy,
            "tres_used": copy,
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
                translator = NODE_FIELD_MAP.get(k, None)

                if translator is not None:
                    # Translate using the translator retrieved from the fields map
                    translator(k, v, res_entity)

                # If no translator has been provided: ignore the field

            yield res_entity
