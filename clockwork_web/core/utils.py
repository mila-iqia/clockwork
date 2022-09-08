"""
Gathers useful functions that can be used by the browser routes and the
REST API.
"""


def to_boolean(arg):
    """
    Transforms a string (or int) arg into a boolean.

    Parameters:
        - arg: The element to transform into boolean. Its expected values are "True",
          "true" or 1 for a return as True; but any "true" non case-sensitive
          will return True. For a return as False, the expected values are
          "false", "False", 0 or None; but False is the default returned value.
          Thus, False is returned with any other cases.

    Returns:
    - True if the input arg is "true", "True", 1 or "1"
    - False otherwise
    """
    if str(arg).lower() in ["true", "1"]:
        return True
    else:
        return False


def get_custom_array_from_request_args(request_arg):
    """
    Create an array from a string by splitting it with its commas.
    Thus, a string of the format "item1,item2,item3" as input parameter
    would cause the following output: ["item1", "item2", "item3"].

    Parameters:
        - request_arg     The string to parse in order to get an array

    Returns:
        An array containing one or more strings.
    """
    # Initialise the array
    returned_strings = []

    # For each element of the splitted request_arg, add it to the array
    for str_element in request_arg.split(","):
        if str_element != "":
            returned_strings.append(str_element)

    # Return the array
    return returned_strings
