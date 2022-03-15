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

import dataclasses
import fnmatch
import logging
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import click
from tabulate import tabulate

from . import __version__
from ._config import load_user_settings
from .deploys import find_deploy_scripts
from .host import (
    _DEFAULT_WAIT as DEFAULT_DISCOVERY_TIMEOUT,
    AddressType,
    find_hosts_on_local_network,
    Host,
    resolve as resolve_host,
)
from .ssh import figure_out_ssh_parameters, interactive_ssh_shell
from .utils import (
    AttrDict,
    IdentifierOrKeyValue,
    multi_choice_prompt,
    single_choice_prompt,
    temp_python_files,
    json_dumps,
)


logging.basicConfig(level=logging.WARNING)


_ERR = click.style("Error:", fg="bright_red", bold=True)

_RE_IF_GLOB = re.compile(r"\[[^\]]+\]|\*|\?", re.ASCII)


def click_hosts_option(f):
    return click.option(
        "--host", "-h", "hosts",
        type=Host.from_str,
        multiple=True,
        metavar="<address>",
    )(f)


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
@click.option("--verbose", default=False, is_flag=True)
@click.option("--pyinfra-verbose", default=False, is_flag=True)
def main(
    ctx,
    discovery_timeout,
    ssh_user,
    ssh_password,
    ssh_port,
    ssh_key,
    ssh_key_password,
    verbose,
    pyinfra_verbose,
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
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    ctx.obj.pyinfra_verbose = pyinfra_verbose


@main.command(help="Run one or more deploy scripts.")
@click.pass_obj
@click_hosts_option
@click.option("-y", "--dont-ask", default=False, is_flag=True)
@click.option("-x", "--enable-regex", default=False, is_flag=True)
@click.option("--dry-run", default=False, is_flag=True)
@click.argument("parameters", type=IdentifierOrKeyValue(), nargs=-1)
def run(obj, hosts, dont_ask, enable_regex, dry_run, parameters):
    # Collect scripts and parameters.
    deploy_scripts, deploy_script_params = get_scripts_and_params(parameters)

    hosts, is_discovered = get_hosts(hosts, obj.discovery_timeout, enable_regex)
    if not dont_ask and is_discovered:
        hosts = select_hosts(hosts)

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

            cmd = ["pyinfra", "--fail-percent", "0"]
            if obj.pyinfra_verbose:
                cmd.append("-vvv")
            if dry_run:
                cmd.append("--dry")
            cmd += [fd.name, script["path"]]

            subprocess.call(cmd)


def get_scripts_and_params(parameters):
    current_script = None
    scripts = []
    script_params = {}

    for key, value in parameters:
        if value is None:
            scripts.append(key)
            current_script = key
            script_params[current_script] = {}
        else:
            try:
                script_params[current_script][key] = value
            except KeyError:
                fatal("a parameter cannot occur before a deploy script")

    return (scripts, script_params)


def _find_deploy_scripts(names):
    deploy_scripts = find_deploy_scripts(names)

    want = set(str(n) for n in names)
    found = set([s["id"] for s in deploy_scripts])
    not_found = want - found

    return (deploy_scripts, not_found)


@main.command(help="Discover hosts on the local network.")
@click.pass_obj
@click_hosts_option
@click.option("-x", "--enable-regex", default=False, is_flag=True)
@click.option("-j", "--output-json", default=False, is_flag=True)
def discover(obj, hosts, enable_regex, output_json):
    hosts, _ = get_hosts(hosts, obj.discovery_timeout, enable_regex)
    if output_json:
        click.echo(json_dumps(hosts))
    else:
        list_hosts(hosts)


@main.command(help="List all builtin and user deploy scripts.")
@click.argument("deploy_scripts", type=click.Path(path_type=Path), nargs=-1)
@click.option(
    "--details",
    default=False,
    is_flag=True,
    help="Show name, description and paramaters for each deploy script.",
)
def info(deploy_scripts, details):
    deploy_scripts = find_deploy_scripts(deploy_scripts)

    for script in deploy_scripts:
        script_id = f"{script['id']} [{script['type'].name.lower()}]"

        if not details:
            click.echo(script_id)
            continue

        view = []

        view.append(("ID:", script_id))
        if v := script.get("name"):
            view.append(("Name:", v))
        if v := script.get("description"):
            view.append(("Description:", v))

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
@click_hosts_option
@click.option("-x", "--enable-regex", default=False, is_flag=True)
def shell(obj, hosts, enable_regex):
    hosts, is_discovered = get_hosts(hosts, obj.discovery_timeout, enable_regex)
    if is_discovered or len(hosts) > 1:
        host = select_host(hosts)
    else:
        host = hosts[0]
    host = get_ssh_params_for_host(host, obj.ssh_parameter_set)
    interactive_ssh_shell(host.ssh_host, host.ssh_params)


@main.command(help="Show version.")
def version():
    click.echo(__version__)


@main.command(help="Resolve a (zeroconf) hostname.")
@click.argument("host", type=Host.from_str, nargs=1)
@click.option("-j", "--output-json", default=False, is_flag=True)
def resolve(host: Host, output_json: bool):
    new_host = resolve_host(host)
    if new_host:
        data = {"results": [a.s for a in new_host.resolved_addrs]}
    else:
        data = {"warning": [f"cannot resolve {host.addr.s}"]}

    if output_json:
        click.echo(json_dumps(data))
    else:
        if results := data.get("results"):
            for a in results:
                click.echo(a)
        elif warning := data.get("warning"):
            for w in warning:
                click.echo(f"WARNING: {w}")
        else:
            raise ValueError(f"unexpected data: {data!r}")


def list_hosts(hosts, showindex=False):
    """List hosts in a table."""
    headers = ["Server", "IPv4", "IPv6", "Hardware ID"]
    rows = []

    for h in hosts:
        addrs = defaultdict(list)
        addrs[h.addr.t].append(h.addr.s)
        for a in h.resolved_addrs:
            addrs[a.t].append(a.s)

        rows.append((
            " ".join(addrs[AddressType.ZEROCONF_SERVER_NAME]) or "N/A",
            " ".join(addrs[AddressType.IPv4]) or "N/A",
            " ".join(addrs[AddressType.IPv6]) or "N/A",
            h.props.get("hardware_id") or "N/A",
        ))

    kwargs = {}
    if showindex:
        kwargs["showindex"] = range(1, len(hosts) + 1)

    click.echo(tabulate(rows, headers=headers, **kwargs))


def write_inventory(fd, hosts, host_data):
    fd.write("hosts = [\n")
    for host in hosts:
        data = {
            **host.ssh_params,
            **host_data,
        }
        # If we're using a zeroconf server name to reference a host,
        # we'll pass it to pyinfra so we can use it in deploy scripts.
        # See horus_deploy.operations.system.reboot for an example.
        if host.addr.t == AddressType.ZEROCONF_SERVER_NAME:
            data["zeroconf_server_name"] = host.addr.s
        data = {k: str(v) for k, v in data.items()}
        fd.write(f"    ({str(host.ssh_host)!r}, {data!r}),\n")
    fd.write("]\n")
    fd.flush()


def get_ssh_params_for_hosts(hosts: List[Host], ssh_parameter_set: Dict[str, str]):
    return [get_ssh_params_for_host(h, ssh_parameter_set) for h in hosts]


def get_ssh_params_for_host(host: Host, ssh_parameter_set: Dict[str, str]):
    resolved_host = resolve_host(host)

    if not resolved_host:
        fatal(f"cannot resolve address for host {host.addr.s}")
        return

    for addr in resolved_host.resolved_addrs:
        ssh_params = figure_out_ssh_parameters(addr.s, ssh_parameter_set)
        if ssh_params:
            resolved_host = dataclasses.replace(
                resolved_host,
                ssh_host=addr.s,
                ssh_params=ssh_params,
            )
            break

    if not resolved_host.ssh_params:
        fatal(f"cannot find SSH parameters for {resolved_host.addr.s}")

    return resolved_host


def fatal(message: str):
    click.echo(f"--> {_ERR} {message}")
    sys.exit(1)


def select_hosts(hosts: List[Host]) -> List[Host]:
    click.echo("")
    list_hosts(hosts, showindex=True)
    click.echo("")
    hosts = multi_choice_prompt(
        "    Select multiple hosts (comma/space separated)", hosts
    )
    click.echo("")
    return hosts


def select_host(hosts: List[Host]) -> Host:
    click.echo("")
    list_hosts(hosts, showindex=True)
    click.echo("")
    host = single_choice_prompt("    Select a device", hosts)
    click.echo("")
    return host


def get_hosts(
    hosts: List[Host],
    discovery_timeout: float = DEFAULT_DISCOVERY_TIMEOUT,
    enable_regex: bool = False,
) -> Tuple[List[Host], bool]:
    filters = []

    if enable_regex:
        try:
            filters = [re.compile(h.addr.s) for h in hosts]
        except re.error as e:
            fatal(f"regular expression {e.pattern!r} is incorrect: {e}")
    elif is_host_glob_filter(hosts):
        filters = [re.compile(fnmatch.translate(h.addr.s)) for h in hosts]
    elif hosts:
        return (hosts, False)

    hosts = find_hosts_on_local_network(discovery_timeout)

    if filters:
        hosts = [
            h
            for h in hosts
            if any(
                f.match(h.addr.s)
                or any(f.match(ra.s) for ra in h.resolved_addrs)
                for f in filters
            )
        ]

    if not hosts:
        fatal("no hosts found")

    return (hosts, True)


def is_host_glob_filter(hosts: List[Host]) -> bool:
    return any(_RE_IF_GLOB.search(h.addr.s) for h in hosts)
