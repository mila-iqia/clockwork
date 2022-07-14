#######################################################################
# Don't edit this file, edit clockwork_web/config.py and copy it back #
#######################################################################

import os
import copy
import zoneinfo

import toml

# This is a marker to indicate no default value
_NoDefault = object()

# format: {key1: value, key2: {key3: value, ...}, ...}
_config = None

# format: {key1: (value, validator), key2: {key3: (value, validator), ...}, ...}
_defaults = {}

_config_file = os.environ.get("CLOCKWORK_CONFIG", None)


class ConfigError(Exception):
    def __init__(self, message, keys=None):
        self.message = message
        self.keys = [] if keys is None else keys

    def __str__(self):
        return f"In key {'.'.join(reversed(self.keys))}: {self.message}"


# Placeholder for validation
def anything(value):
    return value


def string(value):
    if not isinstance(value, str):
        raise ConfigError("expected string")
    return value


def optional_string(value):
    if value is False:
        return value
    return string(value)


def boolean(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        if value in ["True", "true"]:
            return True
        elif value in ["False", "false"]:
            return False
    elif isinstance(value, int):
        if value == 1:
            return True
        elif value == 0:
            return False
    raise ConfigError("expected boolean")


def string_list(value):
    if not isinstance(value, list):
        raise ConfigError("expected list")
    if any(not isinstance(v, str) for v in value):
        raise ConfigError("non-strings in list")
    return value


def timezone(value):
    try:
        return zoneinfo.ZoneInfo(value)
    except ValueError:
        raise ConfigError("invalid time zone")
    except zoneinfo.ZoneInfoNotFound:
        raise ConfigError("unknown timezone")


class SubdictValidator:
    """Validate that all keys in a dictionary have a certain format."""

    def __init__(self, fields):
        self._fields = fields

    def add_field(self, name, validator, default=_NoDefault):
        self._fields[name] = (validator, default)

    def __call__(self, value):
        if not isinstance(value, dict):
            raise ConfigError("expected a dictionary value")
        res = {}
        for k, v in value.items():
            if not isinstance(v, dict):
                raise ConfigError("expected a dictionary value", keys=[k])
            sub = {}
            for field_key, (field_valid, field_default) in list(self._fields.items()):
                if field_key not in v:
                    # key not present in config
                    if field_default is _NoDefault:
                        raise ConfigError("missing field", keys=[field_key, k])
                    else:
                        sub[field_key] = field_default
                else:
                    # key is present in config
                    try:
                        sub[field_key] = field_valid(v[field_key])
                    except ConfigError as e:
                        e.keys.extend([field_key, k])
                        raise
            res[k] = sub
        return res


def register_config(key, default=_NoDefault, validator=anything):
    """Register a configuration key.

    The key should be in the <domain>.<name> format, but can have
    multiple levels of dots.

    `default` is the default value for this configuration option. It can
    remain unset and this will cause an error on load if it is not
    present in the configuration file.

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
        value = d[k]
    except KeyError:
        raise KeyError(f"no such config key '{key}'")
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


def _load_config():
    # Load the configuration file, if any, and merge its content with the
    # defaults to form the application configuration.
    global _config
    if _config_file is not None:
        file_dict = toml.load(_config_file)
        _config = _merge_configs(file_dict, _defaults)
    else:
        _config = _cleanup_default(_defaults)


def _merge_configs(new_dict, default_dict):
    # Produce a configuration dictionary from the defaults and configured values
    #
    # The return value will be a dictionary with the same structure as
    # default_dict, but with values from new_dict, if present.
    #
    # Extra keys present in new_dict are ignored.
    res = {}
    for k, v in default_dict.items():
        if k not in new_dict:
            # key not in config
            if isinstance(v, dict):
                try:
                    res[k] = _cleanup_default(v)
                except ConfigError as e:
                    e.keys.append(k)
                    raise
            else:
                if v[0] is _NoDefault:
                    raise ConfigError("missing value for", keys=[k])
                else:
                    res[k] = v[0]
        else:
            # key is in config
            try:
                if isinstance(v, dict):
                    if not isinstance(nv, dict):
                        raise ConfigError("expected dictionary", keys=[k])
                    res[k] = _merge_configs(nv, v)
                else:
                    # v[1] is the validator
                    res[k] = v[1](nv)
            except ConfigError as e:
                e.keys.append(k)
                raise
    return res


def _cleanup_default(default_dict):
    # Remove validators and make everything has a value set in a default dict
    # for use as configuration.
    res = {}
    for k, v in default_dict.items():
        if isinstance(v, dict):
            try:
                res[k] = _cleanup_default(v)
            except ConfigError as e:
                e.keys.append(k)
                raise
        if v[0] is _NoDefault:
            raise ConfigError("missing value for", keys=[k])
        else:
            res[k] = v[0]
    return res
