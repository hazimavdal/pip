from ..env import Environment


class Base:
    class Meta:
        environ: Environment = None


class Field:
    def __init__(self, env_name=None, default=None, nullable=False, cast=lambda x: x):
        self.default = default
        self.cast = cast
        self.nullable = nullable
        self.env_name = env_name

    def __set_name__(self, owner, name):
        assert issubclass(owner, Base), f"{owner.__name__} does not inherit {Base.__name__}"
        assert owner.Meta.environ is not None, "environ is not set on this object"

        self.varname = self.env_name or name.upper()

    def __get__(self, obj: Base, objtype=None):
        return obj.Meta.environ.get(key=self.varname,
                               default=self.default,
                               nullable=self.nullable,
                               mapper=self.cast)

    def __set__(self, obj, value):
        raise AttributeError("cannot set read-only attribute")
