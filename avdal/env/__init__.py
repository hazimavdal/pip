import os
import re
from typing import List
from collections.abc import Mapping, MutableMapping

_envre = re.compile(r'''^(?:export\s*)?([_a-zA-Z][\w_]*)\s*=\s*(.*)$''')
_varexp = re.compile(r'''\{\{(.*?)\}\}''')
_varname = re.compile(r'''^\s*([\w_]+)\s*$''')
_include_re = re.compile(r'''^#include\s+(.*)\s*$''')


class Environment(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def _expand(self, value):
        for var in _varexp.findall(value):
            match = _varname.match(var)
            if not match:
                raise Exception(f"[{var}]: invalid variable name")

            varname = match.group(1)
            if varname not in self:
                raise Exception(f"[{varname}]: unbounded variable")

            value = value.replace(f"{{{{{var}}}}}", self[varname])

        return value

    def union(self, other: Mapping):
        return Environment({**self, **other})

    def get(self, key: str, default=None, nullable=False, mapper=lambda x: x):
        value = self.__dict__.get(key)

        if value is not None:
            return mapper(value)

        if default is None and not nullable:
            raise Exception(f"{key} not found. Declare it as environment variable or provide a default value.")

        return mapper(default)

    def __setitem__(self, key, value):
        self.__dict__[key] = self._expand(value)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self) -> str:
        return "{}({{{}}})".format(type(self).__name__, ', '.join(
            ('{!r}: {!r}'.format(key, value)
             for key, value in self.__dict__.items())))


class DotEnv(Environment):
    def _load_env(self, env_file: str):
        env_file = os.path.abspath(env_file)

        if env_file in self.envs:
            return

        self.envs.add(env_file)

        if not os.path.isfile(env_file):
            return

        with open(env_file, "r") as f:
            for line in f.readlines():
                match = _include_re.match(line)
                if match is not None:
                    file = match.group(1).strip()
                    self._load_env(file)

                match = _envre.match(line)
                if match is not None:
                    key = match.group(1)
                    value = match.group(2).strip('"').strip("'")

                    self[key] = value

        return vars

    def __init__(self, *env_files):
        super(DotEnv, self).__init__()
        self.envs = set()

        for file in env_files:
            self._load_env(file)
