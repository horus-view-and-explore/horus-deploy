# Usage

Here are some usage example. Use the `--help` flag to see all possible
options and subcommands.


## Discover devices on the local network

```
horus-deploy discover
```


## Install a package to a device

```
horus-deploy run \
    -h 192.168.xxx.xxx \
    -h 192.168.yyy.yyy \
    install_package file=htop-2.2.0-r0.aarch64.rpm
```

htop is installed on 192.168.xxx.xxx and 192.168.yyy.yyy. When the `-h`
option is omitted. horus-deploy looks on the local network and shows a
selection menu with all the devices it found.


## SSH authentication options

```
horus-deploy \
    --ssh-user bert \
    --ssh-key ~/.ssh/demo_key_id_ed25519 \
    run \
    -h 192.168.xxx.xxx \
    install_package file=htop-2.2.0-r0.aarch64.rpm
```
