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

import logging
import os
import pkg_resources
import platform
import shutil
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.ed25519key import Ed25519Key
from paramiko.ssh_exception import AuthenticationException

from ._config import user_config_dir


logger = logging.getLogger(__name__)


_DEFAULT_PRIVATE_KEY_FN = "default_id_ed25519"
_DEFAULT_PUBLIC_KEY_FN = "default_id_ed25519.pub"
_PKG_DEFAULT_PRIVATE_KEY_PATH = pkg_resources.resource_filename(
    __name__, _DEFAULT_PRIVATE_KEY_FN
)
_PKG_DEFAULT_PUBLIC_KEY_PATH = pkg_resources.resource_filename(
    __name__, _DEFAULT_PUBLIC_KEY_FN
)
_DEFAULT_PRIVATE_KEY_PATH = user_config_dir() / _DEFAULT_PRIVATE_KEY_FN
_DEFAULT_PUBLIC_KEY_PATH = user_config_dir() / _DEFAULT_PUBLIC_KEY_FN
_USER_PRIVATE_KEY_PATH = user_config_dir() / "id_ed25519"
_USER_PUBLIC_KEY_PATH = user_config_dir() / "id_ed25519.pub"

_PARAMETER_SETS = [
    {"ssh_user": "root"},
    {"ssh_user": "root", "ssh_key": str(_USER_PRIVATE_KEY_PATH)},
    {"ssh_user": "root", "ssh_key": _DEFAULT_PRIVATE_KEY_PATH},
]


def _setup_default_keys():
    paths = [
        (_PKG_DEFAULT_PRIVATE_KEY_PATH, _DEFAULT_PRIVATE_KEY_PATH),
        (_PKG_DEFAULT_PUBLIC_KEY_PATH, _DEFAULT_PUBLIC_KEY_PATH),
    ]

    for src, dst in paths:
        if not dst.exists():
            shutil.copy(src, dst)
            _set_permissions(dst)


def _set_permissions(path):
    if platform.system() == "Windows":
        username = os.environ["USERNAME"]
        subprocess.run(["icacls", str(path), "/inheritance:r"], check=True)
        subprocess.run(["icacls", str(path), "/grant:r", f"{username}:(R)"], check=True)
    else:
        os.chmod(path, 0o600)


_setup_default_keys()


def figure_out_ssh_parameters(address, extra_set=None):
    """Figure out which SSH connect parameters for host.

    Tries to connect to a host using the parameters in
    ``_PARAMETER_SETS``. Returns the parameters that work.
    """
    parameter_sets = _PARAMETER_SETS
    if extra_set:
        extra_set.setdefault("ssh_user", "root")
        parameter_sets = [extra_set] + parameter_sets

    params = None

    for params in parameter_sets:
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy)

        logger.debug(f"figure_out_ssh_parameters: trying {address=} with {params=}")

        ssh_key = params.get("ssh_key")
        if ssh_key and not os.path.exists(ssh_key):
            logger.debug(
                f"figure_out_ssh_parameters: {ssh_key=} does not exist, skipping"
            )
            continue

        try:
            client.connect(
                address,
                allow_agent=True,
                look_for_keys=True,
                **_to_paramiko_kwargs(params),
            )
            client.close()
        except AuthenticationException:
            logger.debug(
                f"figure_out_ssh_parameters: unable to connect to {address=} with {params=}"
            )
            params = None
        else:
            break

    logger.debug(f"figure_out_ssh_parameters: connected to {address=} with {params=}")

    return params


def load_key_pair():
    """Load key pair from user config directory.

    A new key pair is generated when no key pair exists.

    Returns a 2-element tuple with a private key and a public key as
    strings.
    """
    if not _USER_PRIVATE_KEY_PATH.exists() and not _USER_PUBLIC_KEY_PATH.exists():
        private_key, public_key = _generate_key_pair()
        _USER_PRIVATE_KEY_PATH.write_text(private_key)
        _USER_PUBLIC_KEY_PATH.write_text(public_key)
        os.chmod(_USER_PRIVATE_KEY_PATH, 0o600)
        os.chmod(_USER_PUBLIC_KEY_PATH, 0o644)
        logger.debug(
            "load_key_pair: generated key pair, located at "
            "{_USER_PRIVATE_KEY_PATH} and {_USER_PUBLIC_KEY_PATH}"
        )
    else:
        private_key = _USER_PRIVATE_KEY_PATH.read_text()
        public_key = _USER_PUBLIC_KEY_PATH.read_text()
        logger.debug(
            "load_key_pair: load key pair, located at "
            "{_USER_PRIVATE_KEY_PATH} and {_USER_PUBLIC_KEY_PATH}"
        )

    return (private_key, public_key)


def _generate_key_pair():
    private_key = Ed25519PrivateKey.generate()
    private_str = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption(),
    ).decode("utf-8")

    public_key = private_key.public_key()
    public_str = public_key.public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    ).decode("utf-8")

    return (private_str, public_str)


def get_default_public_key():
    with open(_DEFAULT_PUBLIC_KEY_PATH, "r") as fd:
        return fd.read()


def interactive_ssh_shell(address, ssh_params):
    cmd = ["ssh"]

    if v := ssh_params.get("ssh_key"):
        cmd += ["-i", f"{v}"]
    if v := ssh_params.get("ssh_port"):
        cmd += ["-p", f"{v}"]

    if "ssh_password" in ssh_params:
        raise RuntimeError("password not supported for SSH shell")
    if "ssh_key_password" in ssh_params:
        raise RuntimeError("key password not supported for SSH shell")

    cmd += [f"{ssh_params['ssh_user']}@{address}"]

    subprocess.run(cmd)


def _to_paramiko_kwargs(params):
    mapping = {
        "ssh_user": ("username", lambda v: v),
        "ssh_key": ("pkey", Ed25519Key.from_private_key_file),
        "ssh_password": ("password", lambda v: v),
        "ssh_key_password": ("passphrase", lambda v: v),
        "ssh_port": ("port", lambda v: v),
    }
    kwargs = {}

    for k, v in params.items():
        kwargs[mapping[k][0]] = mapping[k][1](v)

    return kwargs
