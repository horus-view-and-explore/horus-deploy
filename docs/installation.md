# Installation

## Linux

Follow [Using Python on Unix platforms][pyunix].


## Windows

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


### SSH

This applies to both Linux and Windows.

Generate an default SSH key if there isn't one already, e.g. `ssh-keygen -t ed25519`.


## Install horus-deploy

### Using pip

You can install horus-deploy directly from GitHub:

```
pip install "https://github.com/horus-view-and-explore/horus-deploy/archive/refs/heads/main.zip"
```

Or the following when you have git installed:


```
pip install "git+https://github.com/horus-view-and-explore/horus-deploy.git#egg=horus_deploy"
```

Alternatively, you can clone the repository, go into the horus-deploy
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


### Nix / NixOS

For nix we supply a [flake.nix](flake.nix).

To use the flake, add it to your inputs. Then, in your configuration you
can reference `horus-deploy.packages.${system}.horus-deploy`, or add
`horus-deploy.overlays.${system}` to `nixpkgs.overlays` and add
`pkgs.horus-deploy` to your `environment.systemPackages` or
`home.packages`.

This is an example `flake.nix` on how to install it using [home-manager][]:

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

[pyunix]: https://docs.python.org/3/using/unix.html
[pywin]: https://docs.python.org/3/using/windows.html
[pywinenv]: https://docs.python.org/3/using/windows.html#setting-envvars
[home-manager]: https://github.com/nix-community/home-manager
