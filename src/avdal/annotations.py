import inspect
import typing as t
from inspect import Parameter


def enforce_types(f: t.Callable) -> t.Callable:
    def wrapper(*args, **kwargs):
        checks = {}
        sig = inspect.signature(f)
        i = 0
        argc = len(args)
        for k, v in sig.parameters.items():
            if k in kwargs:
                checks[k] = (v.annotation, kwargs[k])
            elif argc > 0:
                checks[k] = (v.annotation, args[i])
                i += 1
                argc -= 1

        for arg, (annotation, value) in checks.items():
            if annotation == Parameter.empty:
                continue

            if annotation is not any and annotation != type(value):
                fn = f.__name__
                e = annotation.__name__
                a = type(value).__name__

                raise ValueError(f"{fn}: param {arg} expects a value of type {e}, got {a}")

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper
