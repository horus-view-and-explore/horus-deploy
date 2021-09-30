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

from urllib.parse import urlparse

from pyinfra.api import operation
from pyinfra.operations import files, server


@operation
def remount(paths, mode, state=None, host=None):
    """Remount mount points in rw or ro mode.

    Parameters:
        paths: A list of paths to moint points.
        mode: rw (read-write) or ro (read-only).
    """
    for path in paths:
        yield server.mount(
            path,
            mounted=True,
            options=["remount", mode],
            state=state,
            host=host,
        )


@operation
def transfer(src, dest, state=None, host=None):
    """Transfer a file to the target host.

    Parameters:
        src: A local path or url (HTTP(S)) to a file.
        dest: A destination path on the target host.
    """
    kw = {"state": state, "host": host}
    scheme = urlparse(src).scheme

    if scheme in ["http", "https"]:
        yield files.download(src=src, dest=dest, **kw)
    else:
        yield files.put(src=src, dest=dest, **kw)
