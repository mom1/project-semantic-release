"""Helpers to read settings from setup.cfg or pyproject.toml."""
import logging
from functools import wraps
from typing import Any

from dynaconf import Dynaconf

from .helpers import import_path

logger = logging.getLogger(__name__)


def _config(root_path=None):
    config_ = Dynaconf(
        root_path=root_path,
        enviromnets=False,
        envvar_prefix="PSR",
        settings_files=["setup.cfg", "pyproject.toml", ".secrets.toml"],
    )

    config_.configure(LOADERS_FOR_DYNACONF=["semantic_release.cfg_loader", "dynaconf.loaders.env_loader"])
    result = Dynaconf(enviromnets=False, envvar_prefix="PSR", root_path=root_path)
    data = {**config_.SEMANTIC_RELEASE.to_dict()}
    tool = config_.get("TOOL", {}).get("SEMANTIC_RELEASE")
    if tool:
        data.update(tool.to_dict())
    result.configure(**data)
    return result


config = _config()


def import_from_settings(settings_name: str) -> Any:
    val = config.get(settings_name)
    if val and isinstance(val, (list, tuple, set)):
        new_val = []
        for v in val:
            if isinstance(v, str):
                new_val.append(import_path(v))
            else:
                break
        else:
            val = config[settings_name] = new_val
    elif val and isinstance(val, str):
        val = config[settings_name] = import_path(val)
    return val


def overload_configuration(func):
    """This decorator gets the content of the "define" array and edits "config" according to the pairs of key/value."""

    @wraps(func)
    def wrap(*args, **kwargs):
        if "define" in kwargs:
            for defined_param in kwargs["define"]:
                pair = defined_param.split("=", maxsplit=1)
                if len(pair) == 2:
                    config[str(pair[0])] = pair[1]
        return func(*args, **kwargs)

    return wrap
