import os
import re
from . import annotations

_envre = re.compile(r'''^(?:export\s*)?([_a-zA-Z][\w_]*)\s*=\s*(.*)$''')
_varexp = re.compile(r'''\{\{(.*?)\}\}''')
_varname = re.compile(r'''^\s*([\w_]+)\s*$''')
_include_re = re.compile(r'''^#include\s+(.*)\s*$''')


def expandvars(value):
    for var in _varexp.findall(value):
        match = _varname.match(var)
        if not match:
            raise Exception(f"[{var}]: invalid variable name")

        varname = match.group(1)
        if varname not in os.environ:
            raise Exception(f"{varname}: unbounded variable")

        value = value.replace(f"{{{{{var}}}}}", os.environ.get(varname))

    return value


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

                os.environ[key] = expandvars(value)


class Env:
    def __init__(self, prefix=None):
        self.prefix = prefix + "_" if prefix else ""

    @annotations.enforce_types
    def __call__(self, var: str, default: any = None, cast: any = str, nullable=False):
        value = os.environ.get(f"{self.prefix}{var}")

        if value is None:
            value = os.environ.get(var)

        if value is None:
            value = default

        if value is None:
            if nullable:
                return None

            raise Exception(f"{var} [prefix={self.prefix}] not found. Declare it as environment variable or provide a default value.")

        if cast is not str:
            try:
                value = cast(value)
            except ValueError:
                raise Exception(f"cannot cast '{value}' into {cast.__name__}")

        return value
