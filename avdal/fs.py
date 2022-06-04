import os
import re
from queue import Queue
from typing import Iterator


class TraversalOptions:
    def __init__(self, **kwargs):
        self.recursive = kwargs.get("recursive", False)
        self.relative = kwargs.get("relative", False)
        self.inclusion = kwargs.get("inclusion", None)
        self.exclusion = kwargs.get("exclusion", None)
        self.ignore_folders = kwargs.get("ignore_folders", [])
        self.ext = kwargs.get("ext", None)
        self.limit = kwargs.get("limit", None)


def unique_filename(path):
    i = 0
    base, ext = os.path.splitext(path)

    while os.path.exists(path):
        path = f'{base}_c{i}{ext}'
        i += 1

    return path


def ls_files(folder, **kwargs) -> Iterator[os.DirEntry]:
    opts = TraversalOptions(**kwargs)
    q = Queue()

    if not opts.relative:
        folder = os.path.expanduser(folder)
        folder = os.path.expandvars(folder)
        folder = os.path.realpath(folder)

    q.put(folder)

    while not q.empty() and (opts.limit is None or opts.limit > 0):
        for entry in os.scandir(q.get()):
            if opts.recursive and entry.is_dir(follow_symlinks=False):
                _, folder = os.path.split(entry.path)
                if folder.strip(os.sep) not in opts.ignore_folders:
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
    return '_'.join(path.split()).replace('&', "and").replace('-', '_').lower()


def rename_files(dir, func, noop=False, **kwargs):
    for entry in ls_files(dir, **kwargs):
        parent, _ = os.path.split(entry.path)
        target = os.path.join(parent, func(entry.name))

        if noop:
            print(f"{entry.path} -> {target}")
            continue

        if os.path.exists(target):
            target = unique_filename(target)

        if entry.path != target:
            os.rename(entry.path, target)
