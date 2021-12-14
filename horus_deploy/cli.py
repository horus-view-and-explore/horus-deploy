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

import subprocess
import sys
from pathlib import Path
from ipaddress import ip_address

import click
from tabulate import tabulate

from ._config import load_user_settings
from .deploys import find_deploy_scripts, shorten_deploy_script_path
from .discovery import discover_devices
from .ssh import figure_out_ssh_parameters, interactive_ssh_shell
from .utils import (
    AttrDict,
    IdentifierOrKeyValue,
    multi_choice_prompt,
    single_choice_prompt,
    temp_python_files,
)


DEFAULT_DISCOVERY_TIMEOUT = 2.0

_ERR = click.style("Error:", fg="bright_red", bold=True)


@click.group()
@click.pass_context
@click.option(
    "--discovery-timeout",
    default=DEFAULT_DISCOVERY_TIMEOUT,
    type=float,
    show_default=True,
)
@click.option("--ssh-user", type=str)
@click.option("--ssh-password", type=str)
@click.option("--ssh-port", type=int)
@click.option(
    "--ssh-key",
    type=click.Path(exists=True, file_okay=True, resolve_path=True, path_type=Path),
)
@click.option("--ssh-key-password", type=str)
def main(
    ctx, discovery_timeout, ssh_user, ssh_password, ssh_port, ssh_key, ssh_key_password
):
    ctx.ensure_object(AttrDict)
    ctx.obj.settings = load_user_settings()
    ctx.obj.discovery_timeout = discovery_timeout

    ctx.obj.ssh_parameter_set = {}
    if ssh_user:
        ctx.obj.ssh_parameter_set["ssh_user"] = ssh_user
    if ssh_password:
        ctx.obj.ssh_parameter_set["ssh_password"] = ssh_password
    if ssh_port:
        ctx.obj.ssh_parameter_set["ssh_port"] = ssh_port
    if ssh_key:
        if ssh_password:
            fatal("--ssh-key cannot be used in combination with --ssh-password")
        ctx.obj.ssh_parameter_set["ssh_key"] = ssh_key
    if ssh_key_password:
        if not ssh_key:
            fatal("--ssh-key is required when using --ssh-key-password")
        ctx.obj.ssh_parameter_set["ssh_key_password"] = ssh_key_password


@main.command(help="Run one or more deploy scripts.")
@click.pass_obj
@click.option("--host", "-h", "hosts", type=str, multiple=True)
@click.argument("parameters", type=IdentifierOrKeyValue(), nargs=-1)
def run(obj, hosts, parameters):
    current_script = None
    deploy_scripts = []
    deploy_script_params = {}

    # Collect scripts and parameters.
    for key, value in parameters:
        if value is None:
            deploy_scripts.append(key)
            current_script = key
            deploy_script_params[current_script] = {}
        else:
            try:
                deploy_script_params[current_script][key] = value
            except KeyError:
                fatal("a paramater cannot occur before a deploy script")

    # Get hosts and their SSH parameters.
    if not hosts:
        hosts = discover_and_select_devices(obj.discovery_timeout)
    hosts = get_ssh_params_for_hosts(hosts, obj.ssh_parameter_set)

    # Find deploy scripts.
    deploy_scripts, missing_deploy_scripts = _find_deploy_scripts(deploy_scripts)
    if missing_deploy_scripts:
        click.echo(f"--> {_ERR}: Some deploy scripts cannot be found.")
        for s in missing_deploy_scripts:
            click.echo(f"    {s}")
        return

    # Create inventory and run deploys.
    for script in deploy_scripts:
        data = deploy_script_params.get(script["id"], {})

        with temp_python_files("inventory.py") as (fd,):
            write_inventory(fd, hosts, data)
            subprocess.call(
                [
                    "pyinfra",
                    "--fail-percent",
                    "0",
                    "-vvv",
                    fd.name,
                    script["path"],
                ]
            )


def _find_deploy_scripts(names):
    deploy_scripts = find_deploy_scripts(names)

    want = set(str(n) for n in names)
    found = set([s["id"] for s in deploy_scripts])
    not_found = want - found

    return (deploy_scripts, not_found)


@main.command(help="Discover devices on the local network.")
@click.pass_obj
def discover(obj):
    list_devices(discover_devices(obj.discovery_timeout))


@main.command(help="List all builtin and user deploy scripts.")
@click.argument("deploy_scripts", type=click.Path(path_type=Path), nargs=-1)
def info(deploy_scripts):
    deploy_scripts = find_deploy_scripts(deploy_scripts)

    for script in deploy_scripts:
        view = []

        view.append(("ID:", script["id"]))
        if v := script.get("name"):
            view.append(("Name:", v))
        if v := script.get("description"):
            view.append(("Description:", v))

        view.append(
            ("Path:", click.format_filename(shorten_deploy_script_path(script["path"])))
        )

        if v := script.get("parameters"):
            view.append(
                (
                    "Parameters:",
                    tabulate(
                        [(f"{pname}:", pdesc) for pname, pdesc in v.items()],
                        tablefmt="plain",
                    ),
                )
            )

        click.echo(tabulate(view, tablefmt="plain"))
        click.echo("")


@main.command(help="Interactive SSH shell.")
@click.pass_obj
@click.option("--host", "-h", "host", type=str)
def shell(obj, host):
    # Get hosts and their SSH parameters.
    if host:
        hosts = [host]
    else:
        hosts = discover_and_select_devices(obj.discovery_timeout, multiple=False)
    hosts = get_ssh_params_for_hosts(hosts, obj.ssh_parameter_set)

    # Start shell.
    interactive_ssh_shell(**hosts[0])


def discover_and_select_devices(discovery_timeout, multiple=True):
    # Scan network for devices.
    click.echo("--> Scanning network for devices...")
    devices = discover_devices(discovery_timeout)
    if not devices:
        fatal("no devices found")

    # List and select discovered devices.
    click.echo("")
    list_devices(devices, showindex=True)
    click.echo("")
    if multiple:
        devices = multi_choice_prompt(
            "    Select multiple devices (comma/space separated)", devices
        )
    else:
        devices = [single_choice_prompt("    Select a device", devices)]
    click.echo("")

    hosts = [d.addresses for d in devices]

    return hosts


def list_devices(devices, showindex=False):
    """List devices in a pretty table."""
    headers = ("Server", "Name", "IP addresses", "Hardware ID")
    rows = [
        (
            d.server,
            d.name,
            ", ".join([str(a) for a in d.addresses]),
            d.hardware_id or "N/A",
        )
        for d in devices
    ]

    kwargs = {}
    if showindex:
        kwargs["showindex"] = range(1, len(devices) + 1)

    click.echo(tabulate(rows, headers=headers, **kwargs))


def write_inventory(fd, hosts, host_data):
    fd.write("hosts = [\n")
    for host in hosts:
        data = {**host.ssh_params, **host_data}
        data = {k: str(v) for k, v in data.items()}
        fd.write(f"    ({str(host.address)!r}, {data!r}),\n")
    fd.write("]\n")
    fd.flush()


def get_ssh_params_for_hosts(hosts, ssh_parameter_set):
    new_hosts = []

    for host in hosts:
        if isinstance(host, str):
            host = [host]
        result = get_ssh_params_for_ip_addresses(host, ssh_parameter_set)
        new_hosts.append(result)

    return new_hosts


def get_ssh_params_for_ip_addresses(ip_addrs, ssh_parameter_set):
    # Sort IP list to IPv4 addresses are first.
    ip_addrs = sorted(
        [ip_address(i) for i in ip_addrs],
        key=lambda ip: ip.version,
    )

    result = None

    # Try to connect to IPs until it works!
    for ip_addr in ip_addrs:
        ssh_params = figure_out_ssh_parameters(str(ip_addr), ssh_parameter_set)
        if ssh_params is not None:
            result = AttrDict(
                address=ip_addr,
                ssh_params=ssh_params,
            )
            break

    if result is None:
        hosts = [str(v) for v in ip_addrs]
        fatal(f"cannot find SSH parameters for: {', '.join(hosts)}")

    return result


def fatal(message):
    click.echo(f"--> {_ERR} {message}")
    sys.exit(1)
