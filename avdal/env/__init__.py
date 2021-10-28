import os
import re


_envre = re.compile(r'''^(?:export\s*)?([_a-zA-Z][\w_]*)\s*=\s*(.*)$''')
_varexp = re.compile(r'''\{\{(.*?)\}\}''')
_varname = re.compile(r'''^\s*([\w_]+)\s*$''')
_include_re = re.compile(r'''^#include\s+(.*)\s*$''')


class DotEnv:
    def get(self, key, default=None):
        return self.vars.get(key, default)

    def expandvars(self, value):
        for var in _varexp.findall(value):
            match = _varname.match(var)
            if not match:
                raise Exception(f"[{var}]: invalid variable name")

            varname = match.group(1)
            if varname not in self.vars:
                raise Exception(f"{varname}: unbounded variable")

            value = value.replace(f"{{{{{var}}}}}", self.vars.get(varname))

        return value

    def load_env(self, env_file: str):
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
                    self.load_env(file)

                match = _envre.match(line)
                if match is not None:
                    key = match.group(1)
                    value = match.group(2).strip('"').strip("'")

                    self.vars[key] = self.expandvars(value)

    def __init__(self, env_file: str):
        self.vars = {}
        self.envs = set()
        self.load_env(env_file)
