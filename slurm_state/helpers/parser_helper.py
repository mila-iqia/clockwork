"""
This file gathers the function shared by the job parser and the node parser
"""


def copy(k, v, res):
    res[k] = v


def copy_with_none_as_empty_string(k, v, res):
    if v == "":
        res[k] = None
    else:
        copy(k, v, res)


def rename(name):
    def renamer(k, v, res):
        res[name] = v

    return renamer


def copy_and_stringify(k, v, res):
    res[k] = str(v)


def rename_subitems(subitem_dict):
    def renamer(k, v, res):
        for subitem, name in subitem_dict.items():
            res[name] = v[subitem]

    return renamer


def translate_with_value_modification(v_modification, translator, **args):
    """
    This function returns a translator that includes a modification
    on the value which will be transmitted to it

    Parameters:
        v_modification  The function modifying the value before it
                        is transmitted to the translator
        translator      The translator called

    Returns:
        A translator function including the expected value modification
    """
    # Some translator can depend on specific arguments. Thus, we call
    # them before to apply it and get the translator which has to be
    # used
    final_translator = translator(**args)

    # This helper is used to update the value v before applying the
    # translator on the triplet (k, v, res)
    def combiner(k, v, res):
        final_translator(k, v_modification(v), res)

    return combiner


def zero_to_null(v):
    """
    Convert the value from 0 to null

    Parameter:
        v   The values to be converted if appliable

    Return:
        The converted values
    """
    # If a value of v equals 0, transform it to None
    for v_k, v_v in v.items():
        if v_v == 0:
            v[v_k] = None
    # Return v
    return v


def rename_and_stringify_subitems(subitem_dict):
    def renamer(k, v, res):
        for subitem, name in subitem_dict.items():
            res[name] = str(v[subitem])

    return renamer


def join_subitems(separator, name):
    def joiner(k, v, res):
        values = []
        for _, value in v.items():
            values.append(str(value))
        res[name] = separator.join(values)

    return joiner


def extract_tres_data(k, v, res):
    """
    Extract count of the elements present in the value associated to the key "tres"
    in the input dictionary. Such a dictionary would present a structure similar as depicted below:
        "tres": {
            'allocated': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ],
            'requested': [
                {'type': 'cpu', 'name': None, 'id': 1, 'count': 4},
                {'type': 'mem', 'name': None, 'id': 2, 'count': 40960},
                {'type': 'node', 'name': None, 'id': 4, 'count': 1},
                {'type': 'billing', 'name': None, 'id': 5, 'count': 1},
                {'type': 'gres', 'name': 'gpu', 'id': 1001, 'count': 1}
            ]
        }

    The dictionaries (and their associated keys) inserted in the job result by this function
    for this input should be:
        "tres_allocated": {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }
        "tres_requested": {
            "billing": 1,
            "mem": 40960,
            "num_cpus": 4,
            "num_gpus": 1,
            "num_nodes": 1
        }
    """

    def get_tres_key(tres_type, tres_name):
        """
        Basically, this function is used to rename the element
        we want to retrieve regarding the TRES type (as we are
        for now only interested by the "count" of the entity)
        """
        if tres_type == "mem" or tres_type == "billing":
            return tres_type
        elif tres_type == "cpu":
            return "num_cpus"
        elif tres_type == "gres":
            if tres_name == "gpu":
                return "num_gpus"
            else:
                return "gres"
        elif tres_type == "node":
            return "num_nodes"
        else:
            return None

    tres_subdict_names = [
        {"sacct_name": "allocated", "cw_name": "tres_allocated"},
        {"sacct_name": "requested", "cw_name": "tres_requested"},
    ]
    for tres_subdict_name in tres_subdict_names:
        res[tres_subdict_name["cw_name"]] = (
            {}
        )  # Initialize the "tres_allocated" and the "tres_requested" subdicts
        for tres_subdict in v[tres_subdict_name["sacct_name"]]:
            tres_key = get_tres_key(
                tres_subdict["type"], tres_subdict["name"]
            )  # Define the key associated to the TRES
            if tres_key:
                res[tres_subdict_name["cw_name"]][tres_key] = tres_subdict[
                    "count"
                ]  # Associate the count of the element, as value associated to the key defined previously
