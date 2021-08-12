from flask import request

def get_filter_from_request_args(keys_for_filter: list[str]):
    """
    Helper function. Relies on `request` in the correct context
    in order to get the actual values.
    """
    filter = {}
    for k in keys_for_filter:
        v = request.args.get(k, None)
        if v is not None:
            filter[k] = v
    return filter
