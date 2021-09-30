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

from pyinfra import host
from pyinfra.api import OperationError
from pyinfra.operations import server

METADATA = {
    "name": "Mender",
    "description": (
        "Install a Mender artifact, reboot, and commit the upgrade. "
        "The path to the artifact can either be a local file path or "
        "a HTTP(S) URL."
    ),
    "parameters": {
        "install": "File path or URL to mender artifact.",
    },
}


if not host.data.install:
    raise OperationError("install argument not given")

server.shell(
    [
        f"mender install {host.data.install}",
    ]
)

server.reboot()

# TODO: Sanity checks.

server.shell(
    [
        "mender commit",
    ]
)
