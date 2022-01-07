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

import re
from os.path import basename
from time import time

from pyinfra.api import operation
from pyinfra.operations import files, dnf

from . import system


_OVERLAYS = ["/lib", "/usr"]
_RE_RPM_FILENAME = re.compile(r"(.*/)*(.*)-(.*)-(.*?)\.(.*)\.rpm")


@operation
def install(packages, state=None, host=None):
    """Install RPM package on target host.

    Paramaters:
        packages: A list of local paths or URLs to RPM packages.
    """
    tmp = _tmpdir()
    kw = {"state": state, "host": host}

    packages = [(src, f"{tmp}/{basename(src)}") for src in packages]

    yield files.directory(tmp, **kw)
    yield system.remount(_OVERLAYS, "rw", **kw)

    try:
        for src, dest in packages:
            yield system.transfer(src, dest, **kw)
            yield dnf.rpm(dest, **kw)
            yield files.file(dest, present=False, **kw)
    finally:
        yield system.remount(_OVERLAYS, "ro", **kw)
        yield files.directory(tmp, present=False, **kw)


@operation
def uninstall(packages, state=None, host=None):
    """Uninstall RPM package from target host.

    Paramaters:
        packages: A list of paths or urls to RPM packages. The package
            name is extracted from the given paths/urls, which is then
            used to uninstall the package.
    """
    kw = {"state": state, "host": host}

    yield system.remount(_OVERLAYS, "rw", **kw)

    try:
        for package in packages:
            name = _get_name_from_rpm_path(package)
            yield dnf.packages(name, present=False, **kw)
    finally:
        yield system.remount(_OVERLAYS, "ro", **kw)


def _get_name_from_rpm_path(package_path):
    match = _RE_RPM_FILENAME.match(package_path)
    if not match:
        return None
    (_, name, _, _, _) = match.groups()
    return name


def _tmpdir():
    return f"/tmp/deploy-{int(time())}"
