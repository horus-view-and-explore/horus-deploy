import dataclasses
import enum
import re
import time
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import Any, Dict, List, Optional, Union

from zeroconf import ServiceBrowser, Zeroconf


_LOCAL = ".local."
_TYPE = "_zmq._tcp.local."
_DEFAULT_WAIT = 2.0
_URN_PREFIX = b"horus:"

# Zeroconf server name consists of a hostname, a numeric suffix, and
# a `.local.` suffix.
_RE_ZC_SERVER_NAME = re.compile(r"(.+?)(?:-\d+)?\.local\.")


class AddressType(enum.IntEnum):
    ZEROCONF_SERVER_NAME = enum.auto()
    ZEROCONF_NAME = enum.auto()
    HOST_NAME = enum.auto()
    IPv4 = enum.auto()
    IPv6 = enum.auto()


@dataclass
class Address:
    s: str
    t: AddressType = field(init=False)

    def __post_init__(self):
        self.t = AddressType.HOST_NAME

        if self.s.endswith(_TYPE):
            self.t = AddressType.ZEROCONF_NAME
        elif self.s.endswith(_LOCAL):
            self.t = AddressType.ZEROCONF_SERVER_NAME
        else:
            try:
                ip = ip_address(self.s)
                if ip.version == 4:
                    self.t = AddressType.IPv4
                elif ip.version == 6:
                    self.t = AddressType.IPv6
            except ValueError:
                pass


@dataclass
class Host:
    addr: Address
    resolved_addrs: List[Address] = field(default_factory=list)
    props: Dict[str, Any] = field(default_factory=dict)
    ssh_host: str = field(default_factory=str)
    ssh_params: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.addr = self._cast_addr(self.addr)
        self.resolved_addrs = [self._cast_addr(a) for a in self.resolved_addrs]

    def _cast_addr(self, addr: Union[str, Address]) -> Address:
        if not isinstance(addr, Address):
            addr = Address(addr)
        return addr


def resolve(host: Host) -> Optional[Host]:
    if host.addr.t == AddressType.ZEROCONF_NAME:
        raise NotImplementedError
    if host.addr.t != AddressType.ZEROCONF_SERVER_NAME:
        # Don't need to resolve, just copy the addr to keep the behavior
        # the same as the address types do need to be resolved.
        return dataclasses.replace(host, resolved_addrs=[host.addr])

    match = _RE_ZC_SERVER_NAME.match(host.addr.s)
    if not match:
        raise ValueError(f"zeroconf server name is malformed: {host.addr!r}")
    host_name = match.group(1)

    # TODO: Some way to pass timeout.
    discovered_hosts = find_hosts_on_local_network()
    matched_host = None

    for discovered_host in discovered_hosts:
        if discovered_host.addr.s.startswith(
            host_name
        ) and discovered_host.addr.s.endswith(_LOCAL):
            matched_host = discovered_host
            break

    if not matched_host:
        return None

    new_host = dataclasses.replace(
        host,
        resolved_addrs=matched_host.resolved_addrs,
    )

    return new_host


def find_hosts_on_local_network(wait_for=_DEFAULT_WAIT):
    """Discover hosts on the local network using Zeroconf."""
    zeroconf = Zeroconf()
    listener = _Listener()
    ServiceBrowser(zeroconf, _TYPE, listener)
    time.sleep(wait_for)
    zeroconf.close()

    hosts = listener.hosts()
    hosts.sort(key=lambda h: h.addr.s)

    return hosts


class _Listener:
    def __init__(self):
        self._hosts: Dict[str, Host] = {}

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        hwid = self._get_hwid(info)
        try:
            del self._hosts[hwid]
        except KeyError:
            del self._hosts[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)

        if not info.properties[b"urn"].startswith(_URN_PREFIX):
            return

        hwid = self._get_hwid(info)
        key = hwid or name

        self._hosts[key] = Host(
            addr=info.server,
            resolved_addrs=info.parsed_addresses(),
            props={
                "name": name,
                "hardware_id": hwid,
            },
        )

    update_service = add_service

    def _get_hwid(self, info):
        if (hwid := info.properties.get(b"hardware_id")) is not None:
            hwid = hwid.decode("utf-8")
        return hwid

    def hosts(self):
        return list(self._hosts.values())
