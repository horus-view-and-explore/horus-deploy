{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    let
      out = system:
        let
          pkgs = nixpkgs.legacyPackages."${system}";
          pyinfra173 = (import ./nix/pyinfra.nix {
            inherit pkgs;
          });
          horus-deploy = with pkgs; python3Packages.buildPythonApplication
            {
              name = "horus-deploy";

              src = ./.;

              propagatedBuildInputs = with python39Packages; [
                zeroconf
                tabulate
                click
                pyinfra173
              ];

              checkInputs = with python39Packages; [
                pytestCheckHook
                pytest-cov
                coverage
                flake8
              ];
            };
        in
        {

          devShell = pkgs.mkShell { };

          packages = {
            inherit horus-deploy;
          };
          defaultPackage = self.packages."${system}".horus-deploy;

          defaultApp = utils.lib.mkApp {
            drv = self.defaultPackage."${system}";
          };

          overlays = self: super: {
            inherit horus-deploy;
          };

        }; in
    with utils.lib; eachSystem defaultSystems out;

}
