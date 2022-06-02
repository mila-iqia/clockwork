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
