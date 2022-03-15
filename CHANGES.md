# Changes

## 0.6.2

- `resolve` subcommand was broken, the given hosts where not resolved.


## 0.6.1

- Fix command argument escaping in `system.set_time` operation.
- `system.set_time` now accepts `datetime.datetime`, `datetime.date`, 
  and `datetime.time` besides a string.


## 0.6.0

- Add host filters for `run`, `discover`, and `shell` subcommands.
  See "Host filters" in `docs/usage.md` for instructions.
- `shell` subcommand supports multiple `-h` flags. A menu is shown when
  multiple hosts arew provided.
- `discovery` subcommand supports multiple `-h` flags.
- `discovery` subcommand's `--json` option has been renamed to
  `-j/--output-json`.
- `resolve` subcommand's `--json` option has been renamed to
  `-j/--output-json`.
- `diagnostics` deploy script now include the date and time in filename
  of the diagnostics file.
- Add `--dry-run` option to `run` subcommand. This enables dry mode for
  pyinfra.
- Add `set_time`, `set_ntp`, and `set_time_zone` operations to the
  `system` module. The builtin `timedate` deploy script uses these
  operations.
- Type hints added to `horus_deploy.host`.


## 0.5.0

- `--verbose` flag to enable debug logging.
- `--pyinfra-verbose` flag to enable debug logging.
- `info` sub-command shows a compact list by default now. Use
  `info --details` to show deploy script name, description, and
  parameters.
- `info` lists deploy script in order of builtin, user (e.g. inside
  `~/.config/horus/horus_deploy/deploy_scripts` on Linux),
  local (current directory).
- Moved all package metadata from `setup.py` to `setup.cfg`.
- Added `version` sub-command and version information to the `horus_deploy`
  module.
- `-h/--host` flag for `run` and `shell` commands now accept
  zeroconf server names, host names, and IP addresses.
- When using host/device discovery when running `run` and `shell`
  commands (i.e. not passing any `-h/--host` flags) the zeroconf server
  name is used to connect to hosts.
- New `horus_deploy.operations.system.reboot` operation. Reconnects even
  when the host IP address changes when using a zeroconf server name.
- `discover` sub-command now has a `--json` flags that allows for easier
  scripting (e.g. using the `jq` program).
- New `resolve` sub-command that resolves zeroconf server names. Also has
  a `--json` flag.
- Gradual introduction of type hints into the code base.

Example of Zeroconf server name: `imx6qdl-variscite-som-D67B8.local.`.
Be sure to **always** include the trailing dot in the name.


## 0.4.0

- Add instructions and scripts for installing horus-deploy with Nix.
- Add `diagnostics` deploy script. Can be used to fetch diagnostics
  from [Horus' Yocto images][horus-yocto-images].

[horus-yocto-images]: https://embed.horus.nu/


## 0.3.0

- Add `uname` deploy script. Can be used to debug connecting to hosts.
- Allow SSH client to look for the user's SSH keys.
- Bug: authentication with `--ssh-password` did not work.
- Bug: when SSH connect parameters can't found, process crashed because
  hosts variable did not exist.
- Breaking change: rename `deploy` command to `run`.


## 0.2.0

- Remove automatic commit from `mender` deploy script and put it in a
  separate deploy script, `mender_commit`.
- Add horus_deploy.operations sub-module to `setup.py`.


## 0.1.0

- Initial release.
