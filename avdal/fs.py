import os
import re
from queue import Queue


def unique_filename(path):
    i = 0
    base, ext = os.path.splitext(path)

    while os.path.exists(path):
        path = f'{base}_c{i}{ext}'
        i += 1

    return path


def ls_files(dir, recursive=True, absolute=True, inclusion=None, exclusion=None, ext=None, limit=None):
    q = Queue()

    if absolute:
        dir = os.path.abspath(dir)

    q.put(dir)

    while not q.empty() and (limit is None or limit > 0):
        for entry in os.scandir(q.get()):
            if recursive and entry.is_dir(follow_symlinks=False):
                q.put(entry.path)
                continue

            if not entry.is_file(follow_symlinks=False):
                continue

            if ext is not None and not entry.name.endswith(ext):
                continue

            if inclusion and not re.match(inclusion, entry.name):
                continue

            if exclusion and re.match(exclusion, entry.name):
                continue

            if limit is not None:
                limit -= 1
                if limit < 0:
                    break

            yield entry
