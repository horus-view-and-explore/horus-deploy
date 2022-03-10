import dataclasses
import enum
import re
import time
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import Any, Dict, List, Optional, Union

from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, ServiceListener


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

    @classmethod
    def from_str(
        cls,
        addr: str,
        resolved_addrs: Optional[List[str]] = None,
        **kwargs,
    ) -> "Host":
        new_addr = cls._cast_addr(addr)
        if resolved_addrs is None:
            resolved_addrs = []
        new_resolved_addrs = [cls._cast_addr(a) for a in resolved_addrs]
        return cls(new_addr, new_resolved_addrs, **kwargs)

    @staticmethod
    def _cast_addr(addr: Union[str, Address]) -> Address:
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


def find_hosts_on_local_network(wait_for: float = _DEFAULT_WAIT) -> List[Host]:
    """Discover hosts on the local network using Zeroconf."""
    zc = Zeroconf()
    listener = _ServiceListener()
    ServiceBrowser(zc, _TYPE, listener=listener)
    time.sleep(wait_for)
    zc.close()

    # Get hosts from listener and sort by zeroconf server name.
    hosts = listener.hosts()
    hosts.sort(key=lambda h: h.addr.s)

    return hosts


class _ServiceListener(ServiceListener):
    def __init__(self):
        self._hosts: Dict[str, Host] = {}

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)

        if info is not None:
            hwid = self._get_hwid(info)
            if hwid is not None:
                try:
                    del self._hosts[hwid]
                    return
                except KeyError:
                    pass

        del self._hosts[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)

        if info is None:
            return
        if not info.properties[b"urn"].startswith(_URN_PREFIX):
            return

        hwid = self._get_hwid(info)
        key = hwid or name

        self._hosts[key] = Host.from_str(
            addr=info.server,
            resolved_addrs=info.parsed_addresses(),
            props={
                "name": name,
                "hardware_id": hwid,
            },
        )

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.add_service(zc, type_, name)

    def _get_hwid(self, info: ServiceInfo) -> Optional[str]:
        hwid = info.properties.get(b"hardware_id")
        if hwid is not None:
            hwid = hwid.decode("utf-8")
        return hwid

    def hosts(self) -> List[Host]:
        return list(self._hosts.values())
