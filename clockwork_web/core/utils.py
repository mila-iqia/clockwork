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
    # For each element of the splitted request_arg, add it to the array
    if request_arg is not None:
        return [
            element.replace(" ", "")
            for element in request_arg.split(",")
            if len(element)
        ]
    else:
        return []


def get_available_date_formats():
    """
    Define the different date formats available through the web interface.

    Returns:
        A list of strings containing identifiers to the date formats
    """
    return ["words", "unix_timestamp", "YYYY/MM/DD", "DD/MM/YYYY", "MM/DD/YYYY"]


def get_available_time_formats():
    """
    Define the different time formats available through the web interface.

    Returns:
        A list of strings containing identifiers to the time formats
    """
    return ["AM/PM", "24h"]


def normalize_username(username):
    """Add the @mila.quebec suffix to the username if not present."""
    if username and "@" not in username:
        # Default to "@mila.quebec"
        username += "@mila.quebec"
    return username
