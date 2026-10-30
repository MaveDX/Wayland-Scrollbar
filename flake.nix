{
  description = "Invisible gesture & IPC scrollbar for scrolling Wayland compositors (Niri, Umbriel, etc.)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgsFor = system: import nixpkgs { inherit system; };
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = pkgsFor system;
          pkg = pkgs.callPackage ./package.nix { };
        in
        {
          default = pkg;
          wayland-scrollbar = pkg;
          niri-scrollbar = pkg;
        }
      );

      homeManagerModules = {
        default = import ./scrollbar.nix;
        wayland-scrollbar = import ./scrollbar.nix;
        niri-scrollbar = import ./scrollbar.nix;
      };

      nixosModules = {
        default = import ./nixos.nix;
        wayland-scrollbar = import ./nixos.nix;
        niri-scrollbar = import ./nixos.nix;
      };
    };
}
