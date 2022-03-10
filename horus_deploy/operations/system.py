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


import json
import subprocess
from datetime import datetime, date, time
from time import sleep
from typing import List
from urllib.parse import urlparse

from pyinfra.api import (
    operation,
    FunctionCommand,
    OperationError,
    StringCommand,
)
from pyinfra.api.connectors.util import remove_any_sudo_askpass_file
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


# NOTE: Based on pyinfra.operations.server.reboot.
@operation(is_idempotent=False)
def reboot(delay=10, interval=1, reboot_timeout=300, state=None, host=None):
    """
    Reboot the server and wait for reconnection.

    When using a Zeroconf server name (e.g. ``imx6qdl-variscite-som-4F2D7-2.local.``)
    this operation resolves it to an IP address on each connect attempt.
    This allows for devices changing their IP address (e.g. changed network
    configuration) and still reconnect and continue the deploy script.

    Parameters:
        delay: Number of seconds to wait before attempting reconnect.
        interval: Interval (s) between reconnect attempts.
        reboot_timeout: Total time before giving up reconnecting.

    Example:

    .. code:: python

        server.reboot(
            name='Reboot the server and wait to reconnect',
            delay=60,
            reboot_timeout=600,
        )
    """
    # Remove this now, before we reboot the server - if the reboot fails (expected or
    # not) we'll error if we don't clean this up now. Will simply be re-uploaded if
    # needed later.
    def remove_any_askpass_file(state, host):
        remove_any_sudo_askpass_file(host)

    yield FunctionCommand(remove_any_askpass_file, (), {})

    yield StringCommand(
        "reboot", success_exit_codes=[0, -1]
    )  # -1 being error/disconnected

    def wait_and_reconnect(state, host):  # pragma: no cover
        sleep(delay)
        max_retries = round(reboot_timeout / interval)
        server_name = host.data.zeroconf_server_name

        host.connection = None  # remove the connection object
        retries = 0

        while True:
            if server_name:
                addrs = _resolve(server_name)
            else:
                addrs = [host.data.ssh_hostname or host.name]

            if _try_to_connect(host, addrs):
                break

            if retries > max_retries:
                raise Exception(
                    ("Server did not reboot in time (reboot_timeout={0}s)").format(
                        reboot_timeout
                    )
                )

            sleep(interval)
            retries += 1

    yield FunctionCommand(wait_and_reconnect, (), {})


def _try_to_connect(host, addrs):
    for addr in addrs:
        host.name = addr
        host.data.ssh_hostname = addr
        host.connect(show_errors=False)
        if host.connection:
            return True
    return False


def _resolve(name: str) -> List[str]:
    # Run the resolver in a different process, because the gevent is used
    # internally in pyinfra break zeroconf. `zeroconf.get_service_info()`
    # just returns `None` all the time.
    p = subprocess.run(
        ["horus-deploy", "resolve", "--output-json", name],
        capture_output=True,
    )

    if p.returncode != 0:
        raise OperationError(f"resolve failed: {p.stdout=} {p.stderr=}")

    data = json.loads(p.stdout)

    if warning := data.get("warning"):
        for w in warning:
            print(f"WAITING: {w}")
        data = []
    elif results := data.get("results"):
        data = results

    return data


@operation
def set_time(date_and_or_time, state=None, host=None):
    if isinstance(date_and_or_time, str):
        allowed_formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%H:%M:%S",
        )

        for fmt in allowed_formats:
            try:
                datetime.strptime(date_and_or_time, fmt)
                break
            except ValueError:
                pass
        else:
            raise OperationError("date time format is not correct")
    elif isinstance(date_and_or_time, datetime):
        date_and_or_time = date_and_or_time.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(date_and_or_time, date):
        date_and_or_time = date_and_or_time.strftime("%Y-%m-%d")
    elif isinstance(date_and_or_time, time):
        date_and_or_time = date_and_or_time.strftime("%H:%M:%S")
    else:
        raise TypeError("only str, datetime, date, and time types allowed")

    yield StringCommand("timedatectl", "set-time", f"'{date_and_or_time}'")


@operation
def set_ntp(enable: bool, state=None, host=None):
    toggle = "true" if enable else "false"
    yield StringCommand("timedatectl", "set-ntp", toggle)


@operation
def set_time_zone(time_zone: str, state=None, host=None):
    yield StringCommand("timedatectl", "set-timezone", time_zone)
