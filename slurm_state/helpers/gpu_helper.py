"""
Functions to help handling the GPU data (namely their conversion from Slurm
to a format used by Clockwork).
"""

import re


def get_cw_gres_description(unparsed_gres, unparsed_features):
    """
    Extract a dictionary presenting the GPU information of the node, from the
    'Gres' and 'AvailableFeatures' fields of the Slurm report

    Parameters:
        - unparsed_gres is the content of the 'Gres' field of the Slurm report
        - unparsed_features is the content of the 'AvailableFeatures' of the
          Slurm report

    Returns:
        A dictionary presenting the following format:
        {
            "cw_name": <cw_name>,
            "name": <gpu_name>,
            "number": <number>,
            "associated_sockets": "<sockets_numbers>" (optional)
        }
        with:
            - <cw_name> a string containing the GPU name according to the
              Clockwork convention
            - <gpu_name> a string containing the GPU name as displayed in the
              Slurm report
            - <number> an integer presenting the number of GPU of this kind on
              the node
            - <sockets_numbers>" a string presenting the sockets associated to
              the GPU. For instance, "(S:0)" if the GPU are associated with
              socket 0, or "(S:0-1)" if associated with sockets 0 and 1.
    """

    # Get gpu name, number and associated sockets
    gpu_specs = get_gres_dict(unparsed_gres)

    if "name" in gpu_specs.keys():
        gpu_specs["cw_name"] = get_cw_gpu_name(gpu_specs["name"], unparsed_features)

    return gpu_specs


def get_gres_dict(slurm_gres_field):
    """
    Convert the Slurm Gres field into a dictionary.

    Parameters:
        - slurm_gres_field is the content of the 'Gres' field in the Slurm report

    Returns:
        An empty dictionary if slurm_gres_field is None.
        Otherwise, a dictionary presenting the following
        format:
            {
                "name": "<gpu_name>",
                "number": <number>,
                "associated_sockets": "<sockets_numbers>" (optional)
            }
            with:
                - <gpu_name> a string containing the GPU name as displayed in the
                  Slurm report
                - <number> an integer presenting the number of GPU of this kind on
                  the node
                - <sockets_numbers>" a string presenting the sockets associated to
                  the GPU. For instance, "(S:0)" if the GPU are associated with
                  socket 0, or "(S:0-1)" if associated with sockets 0 and 1.
    """
    # Return an empty dictionary if the 'Gres' field is None
    if slurm_gres_field == None:
        return {}

    # Return a dictionary describing the "gres" data otherwise
    else:
        # Initialize
        gres_dict = {}
        gres_dict_parsed = {}

        # The Gres field has the following format: "gpu:<gpu_name>:<gpu_number>"
        # with, optionally, at the end: "(S:0)" if the GPU are associated with
        # socket 0, "(S:0-1)" for instance if associated to sockets 0 and 1.
        prog1 = re.compile(r"gpu:(\w*?):(\d+)$")
        prog2 = re.compile(r"gpu:(\w*?):(\d+)\(S:(.*)\)")

        if m := prog1.match(slurm_gres_field):
            # Get the gpu name and number.
            gres_dict_parsed = {"name": m.group(1), "number": int(m.group(2))}
        elif m := prog2.match(slurm_gres_field):
            # Get the gpu name and number, as well as associated sockets
            # if there are any.
            gres_dict_parsed = {
                "name": m.group(1),
                "number": int(m.group(2)),
                "associated_sockets": m.group(3),
            }
        else:
            # We encountered an unexpected expression.
            gres_dict_parsed = {}

        return gres_dict_parsed


def get_cw_gpu_name(slurm_gpu_name, features):
    """
    Return a unique name of the GPU, based on the GPU name of the Slurm report
    and the RAM information in the 'AvailableFeatures' field of the Slurm report.

    The convention used by Clockwork is based on our observation of the
    ComputeCanada's one: a GPU "v100" presenting 32GB of RAM is called "v100l"
    while one presenting 16GB of RAM stays "v100". In a similar way, a "p100"
    presenting 16GB of RAM instead of 12GB is called "v100l".

    Parameters:
        - slurm_gpu_name is the name of the GPU extracted from the Slurm report
        - features presents the content of the field 'AvailableFeatures' of the
          Slurm report

    Returns:
        A string containing the GPU name based on the convention presented above.
    """
    # Parse the 'AvailableFeatures' field
    prog = re.compile(r"(\w*?),(\w*?),([0-9]+)gb$")
    # If the field matches this format, the amount of RAM can be retrieved
    if m := prog.match(features):
        gpu_ram = m.group(3)
        # Change the name if needed
        if slurm_gpu_name == "v100" and gpu_ram == "32":
            return "v100l"
        elif slurm_gpu_name == "p100" and gpu_ram == "16":
            return "p100l"
    return slurm_gpu_name
