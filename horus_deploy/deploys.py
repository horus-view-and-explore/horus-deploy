# Copyright (C) 2021 Horus View and Explore B.V.
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

from pathlib import Path

from ._config import user_config_dir
from .metadata import extract_metadata


_BUILTIN = Path(__file__).parent / "builtin_deploy_scripts"
_USER_DIR = user_config_dir() / "deploy_scripts"


def find_deploy_scripts(deploy_scripts=None):
    """
    Find and load metadata of deploy scripts.

    Locations that are searched are the current directory, the user
    directory, and the horus-deploy built-in deploy scripts directory.

    A list of dictionaries is returned. Each dictionary contains the
    script's metadata (name, description, paramaters), id, and path.
    """
    search_directories = [Path.cwd(), _USER_DIR, _BUILTIN]
    excludes = ["__init__.py"]
    scripts = []
    search_paths = []

    if not deploy_scripts:
        for dir in search_directories:
            if dir.exists():
                search_paths.extend(dir.iterdir())
    else:
        for ds in deploy_scripts:
            for dir in search_directories:
                search_paths.append(dir / ds)

    for fp in search_paths:
        if fp.name in excludes:
            continue
        fp = _fix_path(fp)
        if not fp.exists():
            continue

        metadata = _get_metadata(fp)
        if not metadata:
            continue

        metadata["id"] = fp.parent.stem if fp.name == "deploy.py" else fp.stem
        metadata["path"] = fp

        scripts.append(metadata)

    return scripts


def _fix_path(p):
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


def shorten_deploy_script_path(path):
    path = path.resolve()

    if path.parent == Path.cwd() or path.parent.parent == Path.cwd():
        if path.name == "deploy.py":
            path = path.parent
        path = f"./{path.relative_to(Path.cwd())}"
    elif is_relative_to(path, Path.home()):
        path = f"~/{path.relative_to(Path.home())}"

    return path


def is_relative_to(p, *other):
    try:
        p.relative_to(*other)
        return True
    except ValueError:
        return False
