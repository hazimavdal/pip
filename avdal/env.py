import os
import re
from . import annotations

_envre = re.compile(r'''^(?:export\s*)?([_a-zA-Z][\w_]*)\s*=\s*(.*)$''')
_varre = re.compile(r'''\$([\w_]+)''')
_include_re = re.compile(r'''^#include\s+(.*)\s*$''')


def load_env(env_file: str):
    env_file = os.path.abspath(env_file)
    envs = getattr(os.environ, "__env_files", set())

    if env_file in envs:
        return

    envs.add(env_file)
    os.environ.__env_files = envs

    if not os.path.isfile(env_file):
        return

    with open(env_file, "r") as f:
        for line in f.readlines():
            match = _include_re.match(line)
            if match is not None:
                file = match.group(1).strip()
                load_env(file)

            match = _envre.match(line)
            if match is not None:
                key = match.group(1)
                value = match.group(2).strip('"').strip("'")
                for var in _varre.findall(value):
                    value = value.replace(f"${var}", os.environ.get(var, ""))

                os.environ[key] = value


class Env:
    def __init__(self, prefix=None):
        self.prefix = prefix

    @annotations.enforce_types
    def __call__(self, name: str, default: any = None, cast: type = str, prefixed: bool = True):
        if prefixed and self.prefix:
            name = f"{self.prefix}_{name}"

        value = os.environ.get(name, default=default)

        if value is None:
            raise Exception(f"{name} not found. Declare it as environment variable or provide a default value.")

        if cast is not str:
            try:
                value = cast(value)
            except ValueError:
                raise Exception(f"cannot cast '{value}' into {cast.__name__}")

        return value
