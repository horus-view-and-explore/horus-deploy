# Copyright (C) 2021-2022 Horus View and Explore B.V.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import enum
from pathlib import Path
from typing import List

from ._config import user_config_dir
from .metadata import extract_metadata


_BUILTIN = Path(__file__).parent / "builtin_deploy_scripts"
_USER_DIR = user_config_dir() / "deploy_scripts"


class Type(enum.IntFlag):
    BUILTIN = enum.auto()
    USER = enum.auto()
    LOCAL = enum.auto()


def find_deploy_scripts(filter_by: List = None):
    """
    Find and load metadata of deploy scripts.

    Locations that are searched are the current directory, the user
    directory, and the horus-deploy built-in deploy scripts directory.

    A list of dictionaries is returned. Each dictionary contains the
    script's metadata (name, description, paramaters), id, and path.

    ``filter_by`` limits the search in directories with a list of names.
    """
    search_dirs = [Path.cwd(), _USER_DIR, _BUILTIN]
    excludes = ["__init__.py"]
    scripts = []
    search_paths = []

    # Build scearch paths.
    if filter_by:
        for f in filter_by:
            search_paths.extend([(d / f) for d in search_dirs])
    else:
        for d in search_dirs:
            if d.exists():
                search_paths.extend(d.iterdir())

    # Search for scripts in paths and extract metadata.
    for fp in search_paths:
        if fp.name in excludes:
            continue
        fp = _expand_path(fp)
        if not fp.exists():
            continue

        metadata = _get_metadata(fp)
        if not metadata:
            continue

        metadata["id"] = fp.parent.stem if fp.name == "deploy.py" else fp.stem
        metadata["path"] = fp
        metadata["type"] = _get_type(fp)

        scripts.append(metadata)

    scripts.sort(key=lambda e: (e["type"], e["id"]))

    return scripts


def _expand_path(p):
    if p.is_dir():
        p = p / "deploy.py"
    elif p.suffix != ".py":
        p = p.with_suffix(p.suffix + ".py")
    return p


def _get_metadata(fp):
    try:
        metadata = extract_metadata(fp.read_text())
    except Exception:
        metadata = {}
    return metadata


def _get_type(path):
    if is_relative_to(path, _BUILTIN):
        return Type.BUILTIN
    if is_relative_to(path, _USER_DIR):
        return Type.USER
    if is_relative_to(path, Path.cwd()):
        return Type.LOCAL
    raise ValueError("cannot infer type from {path=}")


def is_relative_to(p, *other):
    try:
        p.relative_to(*other)
        return True
    except ValueError:
        return False
