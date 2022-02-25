import os
import copy

import toml

_config = None
_config_file = os.environ.get("CLOCKWORK_CONFIG", None)

_defaults = {}

_NoDefault = object()


def _get_dict(d, key, create=False):
    keys = key.split(".")
    for k in keys[:-1]:
        if create:
            d = d.setdefault(k, {})
        else:
            d = d[k]
    return d, keys[-1]


def anything(value):
    return value


def register_config(key, default=_NoDefault, validator=anything):
    d, k = _get_dict(_defaults, key, create=True)
    d[k] = (default, validator)


def get_config(key):
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


# This should use the logger at the warning level
def _warn(msg):
    print(msg)


def _merge_configs(new_dict, default_dict):
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
    return {
        k: _cleanup_default(v[0]) if isinstance(v, dict) else v[0]
        for k, v in default_dict
    }


def _load_config():
    global _config
    if _config_file is not None:
        file_dict = toml.load(_config_file)
        _config = _merge_configs(file_dict, _defaults)
    else:
        _config = _cleanup_defaults(_defaults)
