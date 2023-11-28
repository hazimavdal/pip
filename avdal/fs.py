import os
import re
import sys
import json
import requests
from datetime import datetime
from PIL import Image
from queue import Queue
from typing import Iterator


class TraversalOptions:
    def __init__(self, **kwargs):
        self.recursive = kwargs.get("recursive", False)
        self.relative = kwargs.get("relative", False)
        self.inclusion = kwargs.get("inclusion", None)
        self.exclusion = kwargs.get("exclusion", None)
        self.ignore_folders = [
            os.path.realpath(p) for p in kwargs.get("ignore_folders", [])
        ]
        self.ext = kwargs.get("ext", None)
        self.limit = kwargs.get("limit", None)


def unique_filename(path):
    i = 0
    base, ext = os.path.splitext(path)

    while os.path.exists(path):
        path = f"{base}_c{i}{ext}"
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
                folder = os.path.realpath(folder)
                if folder not in opts.ignore_folders:
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


def transform_add_suffix(suffix: str):
    def transform(entry: os.DirEntry):
        return entry.path + suffix

    return transform


def transform_snake_case(entry: os.DirEntry):
    return "_".join(entry.path.split()).replace("&", "and").replace("-", "_").lower()


def transform_with_regex(pattern, repl):
    def transform(entry: os.DirEntry):
        return re.sub(pattern, repl, entry.path)

    return transform


def _transform_exif_date(entry: os.DirEntry, field_id: int):
    try:
        parent, _ = os.path.split(entry)
        _, ext = os.path.splitext(entry)
        field = Image.open(entry.path)._getexif()[field_id]
        sig = datetime.strptime(field, "%Y:%m:%d %H:%M:%S").strftime("%Y%m%d%H%M%S")
        return os.path.join(parent, sig + ext)
    except Exception as _:
        return entry.path


def transform_exif_created_timestamp(entry: os.DirEntry):
    return _transform_exif_date(entry, 36867)


def transform_exif_modified_timestamp(entry: os.DirEntry):
    return _transform_exif_date(entry, 306)


def rename_files(dir, func, noop=False, **kwargs):
    for entry in ls_files(dir, **kwargs):
        target = func(entry)

        if noop:
            print(f"{entry.path} -> {target}")
            continue

        if os.path.exists(target):
            target = unique_filename(target)

        if entry.path != target:
            os.rename(entry.path, target)


def readj(path: str):
    if path == "-":
        return json.load(sys.stdin)
    elif path.startswith("http://") or path.startswith("https://"):
        return requests.get(path).json()
    else:
        with open(path, "r") as f:
            return json.load(f)
