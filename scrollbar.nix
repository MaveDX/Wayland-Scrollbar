{ config, pkgs, lib, ... }:

let
  cfg = config.services.waylandScrollbar;
  legacyCfg = config.services.niriScrollbar;
  defaultPackage = pkgs.callPackage ./package.nix { };

  # Merge legacy niriScrollbar options if used
  enabled = cfg.enable || (legacyCfg.enable or false);
  pkg = if cfg.package != defaultPackage then cfg.package else (legacyCfg.package or cfg.package);
  position = cfg.position;
  offsetArg = if cfg.offset == "auto" then "--offset auto" else "--offset ${toString cfg.offset}";
  height = if cfg.height != 10 then cfg.height else (legacyCfg.height or cfg.height);
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

    offset = lib.mkOption {
      type = lib.types.either lib.types.int (lib.types.enum [ "auto" ]);
      default = "auto";
      description = "Offset in pixels from screen edge, or 'auto' to automatically avoid bars/docks.";
    };

    height = lib.mkOption {
      type = lib.types.int;
      default = 10;
      description = "Height/thickness in pixels of the invisible drag bar.";
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
    height = lib.mkOption {
      type = lib.types.int;
      default = 10;
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
        ExecStart = "${pkg}/bin/wayland-scrollbar --position ${position} ${offsetArg} --height ${toString height} --speed ${toString speed}";
        Restart = "on-failure";
        RestartSec = "3";
      };
    };
  };
}