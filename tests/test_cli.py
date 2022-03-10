from unittest.mock import patch

from horus_deploy import cli
from horus_deploy.host import Host


def test_get_hosts():
    hosts = [
        Host.from_str("192.168.178.125"),
        Host.from_str("192.168.178.60"),
    ]
    new_hosts, is_discovered = cli.get_hosts(hosts)
    assert new_hosts == hosts
    assert not is_discovered


@patch("horus_deploy.cli.find_hosts_on_local_network")
@patch("horus_deploy.cli.sys.exit")
def test_get_hosts_discovered(find_hosts_on_local_network, sys_exit):
    find_hosts_on_local_network.return_value = []
    cli.get_hosts([])
    sys_exit.assert_called_once()


@patch("horus_deploy.cli.find_hosts_on_local_network")
def test_get_hosts_with_glob_filter(find_hosts_on_local_network):
    find_hosts_on_local_network.return_value = [
        Host.from_str("a-b-c.local."),
        Host.from_str("x-y-z.local."),
    ]
    new_hosts, is_discovered = cli.get_hosts([
        Host.from_str("x*"),
    ])
    assert new_hosts == [Host.from_str("x-y-z.local.")]
    assert is_discovered


@patch("horus_deploy.cli.find_hosts_on_local_network")
def test_get_hosts_with_regex_filter(find_hosts_on_local_network):
    find_hosts_on_local_network.return_value = [
        Host.from_str("a-b-c.local."),
        Host.from_str("x-y-z.local."),
        Host.from_str("1-2-3.local."),
    ]
    new_hosts, is_discovered = cli.get_hosts([
        Host.from_str(r"[a-z]-[a-z]-[a-z]\.local\."),
    ], enable_regex=True)
    assert new_hosts == [
        Host.from_str("a-b-c.local."),
        Host.from_str("x-y-z.local."),
    ]
    assert is_discovered
