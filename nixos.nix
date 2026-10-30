{ config, lib, pkgs, ... }:

let
  cfg = config.services.waylandScrollbar;
  legacyCfg = config.services.niriScrollbar;
  defaultPackage = pkgs.callPackage ./package.nix { };

  enabled = cfg.enable || (legacyCfg.enable or false);
  pkg = if cfg.package != defaultPackage then cfg.package else (legacyCfg.package or cfg.package);
in
{
  options.services.waylandScrollbar = {
    enable = lib.mkEnableOption "Wayland Scrollbar system support (uinput permissions and package)";

    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      description = "The wayland-scrollbar package to use.";
    };
  };

  # Legacy alias
  options.services.niriScrollbar = {
    enable = lib.mkEnableOption "Legacy alias for services.waylandScrollbar";
    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      description = "Legacy alias for package.";
    };
  };

  config = lib.mkIf enabled {
    hardware.uinput.enable = true;

    # Grant uinput access to local desktop sessions without manual group assignment or udev editing
    services.udev.extraRules = ''
      KERNEL=="uinput", MODE="0660", GROUP="input", TAG+="uaccess"
    '';

    environment.systemPackages = [ pkg ];
  };
}
