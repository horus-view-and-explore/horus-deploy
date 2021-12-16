# horus-deploy

Deploy configurations to Horus devices.

horus-deploy is a wrapper around [pyinfra][]. In addition to the
functionality pyinfra provides, horus-deploy provides the following:

- Device discovery on local network.
- Automatic SSH parameter selection for deploying to devices.
- Operations and deploy scripts for common actions.

[pyinfra]: https://pyinfra.com/

## Installation

### Linux

Follow [Using Python on Unix platforms][pyunix].

### Windows

1. Install Python 3.9 from the Microsoft Store. Or follow the
   [Using Python on Windows][pywin] guide.

2. Enable UTF-8 for Python by adding `PYTHONUTF8=1` to the environment
   variables.

3. Add Python's script path to the `Path` environment variable. You can
   get the script path by running the following snippet in the
   PowerShell or command prompt:

   ```
   python -c 'import site; print(site.USER_BASE + \"\\Python39\\Scripts\")'
   ```

See [Excursus: Setting environment variables][pywinenv] for instructions
on setting environment variables.

[pyunix]: https://docs.python.org/3/using/unix.html
[pywin]: https://docs.python.org/3/using/windows.html
[pywinenv]: https://docs.python.org/3/using/windows.html#setting-envvars

### Install horus-deploy

#### Using pip

You can install horus-deploy directly from GitHub:

```
pip install "git+https://github.com/horus-view-and-explore/horus-deploy.git#egg=horus_deploy"
```

Alternatively, you can clone the repository, go into the horus-deploy working
directory and run:

```
pip install -U .
```

When you're developing run the following instead:

```
pip install --editable .
```

Changes to the source code then require not reinstall.

NOTE: On Windows `pip` is called with `pip.exe`.

#### Nix / NixOS

For nix we supply a [flake.nix](flake.nix).

To use the flake, add it to your inputs. Then, in your configuration you
can reference `horus-deploy.packages.${system}.horus-deploy`, or add
`horus-deploy.overlays.${system}` to `nixpkgs.overlays` and add
`pkgs.horus-deploy` to your `environment.systemPackages` or
`home.packages`.

This is an example `flake.nix` on how to install it using
[home-manager](https://github.com/nix-community/home-manager):

```nix
{
   inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-21.11";

   inputs.home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
   };

   inputs.horus-deploy = {
      url = "github:horus-view-and-explore/horus-deploy";
      inputs.nixpkgs.follows = "nixpkgs";
   };

   outputs = { nixpkgs, home-manager, horus-deploy }: {
      homeConfigurations = {
         bert = home-manager.lib.homeManagerConfiguration rec {
            system = "x86_64-linux";
            username = "bert";
            homeDirectory = "/home/bert";

            configuration = { pkgs, config, ... }: {
               nixpkgs.overlays = [ horus-deploy.overlays.${system} ];

               home.packages = [
                  pkgs.horus-deploy
               ];
            };
         };
      };
   };
}
```

Then from the same directory call `nix build .#homeConfigurations.bert.activationPackage`.
This builds the nix expression and can be activated by calling `./run/activate`.
Congratulations, you now have installed horus-deploy with the nix package manager!


## Usage

Here are some usage example. Use the `--help` flag to see all possible
options and subcommands.

### Discover devices on the local network

```
horus-deploy discover
```

### Install a package to a device

```
horus-deploy run \
    -h 192.168.xxx.xxx \
    -h 192.168.yyy.yyy \
    install_package file=htop-2.2.0-r0.aarch64.rpm
```

htop is installed on 192.168.xxx.xxx and 192.168.yyy.yyy. When the `-h`
option is omitted. horus-deploy looks on the local network and shows a
selection menu with all the devices it found.

### SSH authentication options

```
horus-deploy \
    --ssh-user bert \
    --ssh-key ~/.ssh/demo_key_id_ed25519 \
    run \
    -h 192.168.xxx.xxx \
    install_package file=htop-2.2.0-r0.aarch64.rpm
```

## Writing deploy scripts

See `horus_deploy/builtin_deploy_scripts` for examples. And see
Pyinfra's documentation on all supported [operations][] and [facts][].

Extra operations are located in `horus_deploy/operations`.

[operations]: https://docs.pyinfra.com/en/1.x/operations.html
[facts]: https://docs.pyinfra.com/en/1.x/facts.html
