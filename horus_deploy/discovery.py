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

import time
from ipaddress import ip_address

from zeroconf import ServiceBrowser, Zeroconf

from .utils import AttrDict


_TYPE = "_zmq._tcp.local."
_DEFAULT_WAIT = 2.0
_URN_PREFIX = b"horus:"


def discover_devices(wait_for=_DEFAULT_WAIT):
    """Discover device on the local network using Zeroconf."""
    zeroconf = Zeroconf()
    listener = Listener()
    ServiceBrowser(zeroconf, _TYPE, listener)
    time.sleep(wait_for)
    zeroconf.close()

    return listener.devices()


class Listener:
    def __init__(self):
        self._devices = {}

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        hwid = self._get_hwid(info)
        try:
            del self._devices[hwid]
        except KeyError:
            del self._devices[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)

        if not info.properties[b"urn"].startswith(_URN_PREFIX):
            return

        hwid = self._get_hwid(info)
        key = hwid or name
        self._devices[key] = AttrDict(
            name=name,
            server=info.server,
            addresses=self._parse_ip_addresses(info.parsed_addresses()),
            hardware_id=hwid,
        )

    update_service = add_service

    def _get_hwid(self, info):
        if (hwid := info.properties.get(b"hardware_id")) is not None:
            hwid = hwid.decode("utf-8")
        return hwid

    def _parse_ip_addresses(self, addresses):
        return [ip_address(addr) for addr in addresses]

    def devices(self):
        devices = list(self._devices.values())
        devices.sort(key=lambda d: d.server)
        return devices
