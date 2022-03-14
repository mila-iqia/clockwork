#######################################################################
# Don't edit this file, edit clockwork_web/config.py and copy it back #
#######################################################################

import os
import copy

import toml

# This is a marker to indicate no default value
_NoDefault = object()

# format: {key1: value, key2: {key3: value, ...}, ...}
_config = None

# format: {key1: (value, validator), key2: {key3: (value, validator), ...}, ...}
_defaults = {}

_config_file = os.environ.get("CLOCKWORK_CONFIG", None)


# Placeholder for validation
def anything(value):
    return value


def register_config(key, default=_NoDefault, validator=anything):
    """Register a configuration key.

    The key should be in the <domain>.<name> format, but can have
    multiple levels of dots.

    `default` is the default value for this configuration option.  It
    can remain unset and this will cause an error on access if it is
    not present in the configuration file (this may change to an error
    on file load in the future).

    `validator` if a function which will get the value read from the
    configuration and should validate that it is an acceptable value
    or transform it to one and return the final value. The returned
    value will be what is reflected in the configuration.
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
    # Note that it will create any missing intermediate dictionaries
    # if `create` is True.
    keys = key.split(".")
    for k in keys[:-1]:
        if create:
            d = d.setdefault(k, {})
        else:
            d = d[k]
    return d, keys[-1]


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
            # In this case we use the value from default_dict since
            # the key is not in new_dict
            if isinstance(v, dict):
                res[k] = _cleanup_default(v)
            else:
                # v[0] is the default value
                res[k] = v[0]
        else:
            # And here we extract and validate the value from new_dict
            if isinstance(v, dict):
                res[k] = _merge_configs(nv, v)
            else:
                # v[1] is the validator
                res[k] = v[1](nv)
    return res


def _cleanup_default(default_dict):
    # Remove validators in a default dict for use as configuration.
    return {
        k: _cleanup_default(v[0]) if isinstance(v, dict) else v[0]
        for k, v in default_dict
    }
