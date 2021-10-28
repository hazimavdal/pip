from typing import List, Iterator
from collections.abc import Mapping


class Base:
    class Meta:
        envs = []

    def add_env(self, env: Mapping):
        self.Meta.envs.append(env)

    @property
    def envs(self) -> Iterator[Mapping]:
        for env in self.Meta.envs:
            yield env


class Field:
    def __init__(self, env_name=None, default=None, nullable=False, mapper=lambda x: x):
        self.default = default
        self.mapper = mapper
        self.nullable = nullable
        self.env_name = env_name

    def __set_name__(self, owner, name):
        self.varname = self.env_name or name.upper()

    def _load_var(self, var, obj: Base, objtype=None):
        for env in obj.envs:
            value = env.get(var)
            if value:
                return value

        return None

    def __get__(self, obj, objtype=None):
        value = self._load_var(self.varname, obj, objtype)

        if value is None:
            value = self.default

        if value is None:
            if self.nullable:
                return None

            raise Exception(f"{self.varname} not found. Declare it as environment variable or provide a default value.")

        return self.mapper(value)

    def __set__(self, obj, value):
        raise AttributeError("cannot set read-only attribute")
