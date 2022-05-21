import os
import re
from queue import Queue


class TraversalOptions:
    def __init__(self, **kwargs):
        self.recursive = kwargs.get("recursive", False)
        self.absolute = kwargs.get("absolute", False)
        self.inclusion = kwargs.get("inclusion", None)
        self.exclusion = kwargs.get("exclusion", None)
        self.ext = kwargs.get("ext", None)
        self.limit = kwargs.get("limit", None)


def unique_filename(path):
    i = 0
    base, ext = os.path.splitext(path)

    while os.path.exists(path):
        path = f'{base}_c{i}{ext}'
        i += 1

    return path


def ls_files(dir, **kwargs):
    opts = TraversalOptions(**kwargs)
    q = Queue()

    if opts.absolute:
        dir = os.path.abspath(dir)

    q.put(dir)

    while not q.empty() and (opts.limit is None or opts.limit > 0):
        for entry in os.scandir(q.get()):
            if opts.recursive and entry.is_dir(follow_symlinks=False):
                q.put(entry.path)
                continue

            if not entry.is_file(follow_symlinks=False):
                continue

            if opts.ext is not None and not entry.name.endswith(opts.ext):
                continue

            if opts.inclusion and not re.match(opts.inclusion, entry.name):
                continue

            if opts.exclusion and re.match(opts.exclusion, entry.name):
                continue

            if opts.limit is not None:
                opts.limit -= 1
                if opts.limit < 0:
                    break

            yield entry


def transform_snake_case(path: str):
    return '_'.join(path.name.split()).replace('&', "and").replace('-', '_').lower()
