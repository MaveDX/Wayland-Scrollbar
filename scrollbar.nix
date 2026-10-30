{ config, pkgs, lib, ... }:

let
  cfg = config.services.waylandScrollbar;
  legacyCfg = config.services.niriScrollbar;
  defaultPackage = pkgs.callPackage ./package.nix { };

  # Merge legacy niriScrollbar options if used
  enabled = cfg.enable || (legacyCfg.enable or false);
  pkg = if cfg.package != defaultPackage then cfg.package else (legacyCfg.package or cfg.package);
  position = cfg.position;
  height = if cfg.height != 1 then cfg.height else (legacyCfg.height or cfg.height);
  speed = if cfg.speed != 12.0 then cfg.speed else (legacyCfg.speed or cfg.speed);
in
{
  options.services.waylandScrollbar = {
    enable = lib.mkEnableOption "Wayland Invisible Scrollbar user service (Niri, Umbriel)";

    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      description = "The wayland-scrollbar package to use.";
    };

    position = lib.mkOption {
      type = lib.types.enum [ "top" "bottom" "left" "right" ];
      default = "top";
      description = "Screen edge to attach the scrollbar to: 'top', 'bottom', 'left', or 'right'.";
    };

    height = lib.mkOption {
      type = lib.types.int;
      default = 1;
      description = "Trigger thickness in pixels at the screen edge (default: 1, strictly on TOP layer, preserves full usage and detection of underlying bars/docks).";
    };

    speed = lib.mkOption {
      type = lib.types.float;
      default = 12.0;
      description = "Trackpad gesture scroll sensitivity multiplier.";
    };
  };

  # Backwards compatibility options
  options.services.niriScrollbar = {
    enable = lib.mkEnableOption "Legacy alias for services.waylandScrollbar";
    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      description = "Legacy alias for package.";
    };
    position = lib.mkOption {
      type = lib.types.enum [ "top" "bottom" "left" "right" ];
      default = "top";
      description = "Legacy alias for position.";
    };
    height = lib.mkOption {
      type = lib.types.int;
      default = 1;
      description = "Legacy alias for height.";
    };
    speed = lib.mkOption {
      type = lib.types.float;
      default = 12.0;
      description = "Legacy alias for speed.";
    };
  };

  config = lib.mkIf enabled {
    home.packages = [ pkg ];

    systemd.user.services.wayland-scrollbar = {
      Unit = {
        Description = "Wayland Invisible Scrollbar Service (Niri, Umbriel)";
        PartOf = [ "graphical-session.target" ];
        After = [ "graphical-session.target" ];
      };

      Install = {
        WantedBy = [ "graphical-session.target" ];
      };

      Service = {
        ExecStart = "${pkg}/bin/wayland-scrollbar --position ${position} --height ${toString height} --speed ${toString speed}";
        Restart = "on-failure";
        RestartSec = "3";
      };
    };
  };
}