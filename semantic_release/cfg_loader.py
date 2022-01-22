from pathlib import Path

import validate
from configobj import ConfigObj
from dynaconf.base import LazySettings
from dynaconf.loaders.base import BaseLoader


def load(obj: LazySettings, env: str = None, silent: bool = True, key: str = None, filename: str = None):
    """"""
    filename = filename or "setup.cfg"
    if not Path(filename).exists():
        filename = " "

    configspec = ConfigObj(
        str(Path(__file__).parent / "defaults.cfg"), interpolation=False, list_values=False, _inspec=True
    )
    validator = validate.Validator()

    def conf_to_dict(cfg):
        cfg.validate(validator)
        return cfg.dict()

    loader = BaseLoader(
        obj=obj,
        env=env,
        identifier="cfg",
        extensions=(".cfg",),
        file_reader=lambda fileobj: conf_to_dict(ConfigObj(fileobj, configspec=configspec)),
        string_reader=lambda strobj: conf_to_dict(ConfigObj(strobj.split("\n"), configspec=configspec)),
    )

    loader.load(
        filename=filename,
        key=key,
        silent=silent,
    )
