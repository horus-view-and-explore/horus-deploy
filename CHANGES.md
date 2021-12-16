# Changes

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
- Add horus_deploy.operations submodule to setup.py.


## 0.1.0

- Initial release.
