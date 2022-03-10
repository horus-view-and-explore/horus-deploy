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


## Host filters

Use host filter to target specific devices. Filters are applied to all
addresses a host has, e.g. zeroconf server names and IP adresses.

There are two types of filters: unix-style glob and regular expressions.
The first is detected automatically when a glob pattern is found
in a `-h` option. The second is explicitly enabled with the `-x` option.

These filter can be used with the `run`, `discover`, and `shell`
subcommands.

See "Unix-style glob reference" below for a reference and
[Python's Regular Expression Syntax][pyre] for a reference on regular
expressions.

[pyre]: https://docs.python.org/3/library/re.html#regular-expression-syntax


### Examples

Filter on Variscite devices:

```
$ horus-deploy discover -h '*variscite*'
Server                                IPv4           IPv6  Hardware ID
------------------------------------  -------------  ----  -------------
imx6qdl-variscite-som-AAA-BBB.local.  192.168.42.5   ...   N/A
imx6qdl-variscite-som-CCC-DDD.local.  192.168.42.5   ...   N/A
```

Or something weirdly specific as all devices with an IP address where
the last octet is above 99:

```
$ horus-deploy discover -x -h '\d+\.\d+\.\d+\.[12]\d{2}'
Server                                          IPv4            IPv6  Hardware ID
----------------------------------------------  -------------   ----  -----------
DESKTOP-AAAAAAA-2.local.                        192.168.42.196  ...   ...
imx6qdl-variscite-som-BBBBB-CCCC.local.         192.168.42.125  ...   N/A
jetson-agx-xavier-devkit-DDDDD-EEEE.local.      192.168.42.135  ...   ...
jetson-tx2-devkit-FFFFF-GGGG.local.             192.168.42.131  ...   ...
jetson-xavier-nx-devkit-emmc-HHHHH-IIII.local.  192.168.42.124  ...   ...
```


## Unix-style glob reference

| Pattern | Meaning                          |
|---------|----------------------------------|
| *       | matches everything               |
| ?       | matches any single character     |
| [seq]   | matches any character in seq     |
| [!seq]  | matches any character not in seq |
