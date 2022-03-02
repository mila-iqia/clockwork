import os
import copy

import toml

# This is a marker to indicate no default value
_NoDefault = object()

_config = None
_defaults = {}
_config_file = os.environ.get("CLOCKWORK_CONFIG", None)


def register_config(key, default=_NoDefault, validator=anything):
    """Register a configuration key.

    The key should be in the <domain>.<name> format, but can have
    multiple levels of dots.
    """
    d, k = _get_dict(_defaults, key, create=True)
    d[k] = (default, validator)


def get_config(key):
    """Get the value for a configuration key.

    The key must have been previously registered with register_config().

    This also triggers the loading and parsing of the configuration
    file when first called. Do not call it at the top level in a file
    otherwise it will prevent other files from registering their
    configuration keys.
    """
    global _config
    if _config is None:
        _load_config()
    try:
        d, k = _get_dict(_config, key)
    except KeyError:
        raise KeyError(f"no such config key '{key}'")
    value = d[k]
    if value is _NoDefault:
        raise KeyError(f"no value set for '{key}'")
    return value


def _get_dict(d, key, create=False):
    # Index into a multi-level dictionary using a dotted name.
    #
    # For d = {'a': {'b': 1, 'c': 2}} and the key 'a.b', this would return
    # ({'b': 1, 'c': 2}, 'b')
    #
    # This is to support modification of the last level dictionary
    #
    # Note that it will create any missing intermediate dictionaries.
    keys = key.split(".")
    for k in keys[:-1]:
        if create:
            d = d.setdefault(k, {})
        else:
            d = d[k]
    return d, keys[-1]


# Placeholder for validation
def anything(value):
    return value


# This should use the logger at the warning level
def _warn(msg):
    print(msg)


def _load_config():
    # Load the configuration file, if any, and merge its content with the
    # defaults to form the application configuration.
    global _config
    if _config_file is not None:
        file_dict = toml.load(_config_file)
        _config = _merge_configs(file_dict, _defaults)
    else:
        _config = _cleanup_defaults(_defaults)


def _merge_configs(new_dict, default_dict):
    # Produce a configuration dictionary from the defaults and configured values
    #
    # The return value will be a dictionary with the same structure as
    # default_dict, but with values from new_dict, if present.
    #
    # Extra keys present in new_dict are ignored.
    res = {}
    for k, v in default_dict.items():
        nv = new_dict.get(k, _NoDefault)
        if nv is _NoDefault:
            if isinstance(v, dict):
                res[k] = _cleanup_default(v)
            else:
                res[k] = v[0]
        else:
            if isinstance(v, dict):
                res[k] = _merge_configs(nv, v)
            else:
                res[k] = v[1](nv)
    return res


def _cleanup_default(default_dict):
    # Cleanup extra values in a default dict for use as configuration.
    return {
        k: _cleanup_default(v[0]) if isinstance(v, dict) else v[0]
        for k, v in default_dict
    }
