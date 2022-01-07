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

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from pyinfra.operations import python

from horus_deploy.ssh import load_key_pair


METADATA = {
    "name": "Install SSH key",
    "description": (
        "Install a public SSH key into ~/.ssh/authorized_keys "
        "on the target device. A SSH key pair is generated "
        "(if none exist) and placed inside the user "
        "configuration directory."
    ),
    "parameters": {
        "keep_default": "Keep the default SSH key (Insecure). Default: false.",
    },
}


DEFAULT_KEY_CHECKSUM = "46f70f3b2a89ce809bf0b1949aca1d51"
AUTHORIZED_KEYS_NAME = "authorized_keys"
AUTHORIZED_KEYS_PATH = f"/home/root/.ssh/{AUTHORIZED_KEYS_NAME}"


def install_public_key(state, host):
    keep_default_key = host.host_data.get("keep_default")

    keys = load_authorized_keys(host)

    if not keep_default_key:
        keys = remove_default_key(keys)

    _, public_key = load_key_pair()
    keys.add(public_key + "\n")

    save_authorized_keys(host, keys)


def load_authorized_keys(host):
    with TemporaryDirectory() as dirname:
        dest = Path(dirname) / AUTHORIZED_KEYS_NAME
        host.get_file(
            remote_filename=AUTHORIZED_KEYS_PATH,
            filename_or_io=str(dest),
        )
        keys = dest.read_text()

    keys = set(keys.splitlines(keepends=True))

    return keys


def save_authorized_keys(host, keys):
    keys = "".join(keys)

    with TemporaryDirectory() as dirname:
        src = Path(dirname) / AUTHORIZED_KEYS_NAME
        src.write_text(keys)
        host.put_file(
            filename_or_io=str(src),
            remote_filename=AUTHORIZED_KEYS_PATH,
        )


def remove_default_key(keys):
    return set([key for key in keys if md5sum(key) != DEFAULT_KEY_CHECKSUM])


def md5sum(key):
    return hashlib.md5(key.encode("utf-8")).hexdigest()


python.call(name="SSH/Install public key", function=install_public_key)
