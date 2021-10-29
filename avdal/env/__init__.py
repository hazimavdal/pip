import os
import re
from typing import List
from collections.abc import Mapping

_envre = re.compile(r'''^(?:export\s*)?([_a-zA-Z][\w_]*)\s*=\s*(.*)$''')
_varexp = re.compile(r'''\{\{(.*?)\}\}''')
_varname = re.compile(r'''^\s*([\w_]+)\s*$''')
_include_re = re.compile(r'''^#include\s+(.*)\s*$''')


class Environment(Mapping):
    def __init__(self, data: Mapping):
        self._data = data

    def union(self, other: Mapping):
        return Environment({**self, **other})

    def get(self, key: str, default=None, nullable=False, mapper=lambda x: x):
        value = self._data.get(key)

        if value is not None:
            return mapper(value)

        if default is None and not nullable:
            raise Exception(f"{key} not found. Declare it as environment variable or provide a default value.")

        return mapper(default)

    def __getitem__(self, k):
        return self._data[k]

    def __iter__(self):
        keys = list(self._data)
        for key in keys:
            yield key

    def __len__(self):
        return len(self._data)

    def __repr__(self) -> str:
        return '({{{}}})'.format(', '.join(
            ('{!r}: {!r}'.format(key, value)
             for key, value in self._data.items())))


class DotEnv(Environment):
    def _expandvars(self, value):
        for var in _varexp.findall(value):
            match = _varname.match(var)
            if not match:
                raise Exception(f"[{var}]: invalid variable name")

            varname = match.group(1)
            if varname not in self.vars:
                raise Exception(f"[{varname}]: unbounded variable")

            value = value.replace(f"{{{{{var}}}}}", self.vars.get(varname))

        return value

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

                    self.vars[key] = self._expandvars(value)

    def __init__(self, *env_files):
        self.vars = {}
        self.envs = set()

        for file in env_files:
            self._load_env(file)

        super(DotEnv, self).__init__(self.vars)
