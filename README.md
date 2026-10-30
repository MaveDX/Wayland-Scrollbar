# Wayland Scrollbar 🖱️

An **invisible screen-edge drag bar** for scrolling Wayland compositors (such as **Niri** and **Umbriel**).

Attached directly to screen edges (**top**, **bottom**, **left**, or **right**) on the **`OVERLAY` layer**, it sits right on top of existing layers in-line with your bar or dock, but utilizes an ultra-thin 1-pixel edge trigger so it **never impedes the usage, clicks, or hover detection** of the bars and docks underneath it.

---

## ✨ Features

- **Direct Screen Edge Attachment**: Attached directly to the screen edge (in-line with your bar or dock) with 0 offset.
- **On Top of Existing Layer (`OVERLAY`)**: Runs on layer `OVERLAY` so it sits above your shell's bar and dock.
- **Zero Collision / Impairment**: Uses an ultra-thin 1-pixel hairline trigger at the physical screen edge ($y=0$):
  - Flinging your mouse to the physical edge lets you click and drag to smoothly scroll your workspaces.
  - Hovering and clicking on your bar buttons, tray icons, menus, and dock icons ($y \ge 1$) works **100% unimpeded** with full hover detection and magnification.
- **Smooth Trackpad Emulation**: Emulates hardware 3-finger swipe gestures via `/dev/uinput` for fluid, continuous scrolling in both Niri and Umbriel.
- **Graceful IPC Fallback**: If `/dev/uinput` permissions are not enabled, it automatically falls back to compositor IPC column navigation without crashing.
- **Multi-Monitor Native**: Spans across all active monitors and automatically updates when displays are connected or disconnected.
- **Mouse Wheel Support**: Rolling the scroll wheel at the edge also scrolls columns.

---

## 🚀 Nix Flakes Setup

### 1. Home Manager (`home.nix`)

```nix
{
  imports = [
    inputs.niri-scrollbar.homeManagerModules.default
  ];

  services.waylandScrollbar = {
    enable = true;
    position = "top";    # "top", "bottom", "left", or "right" (default: "top")
    layer = "overlay";   # "overlay" (sits on top of bar/dock) or "top"
    height = 1;          # 1px edge hairline trigger (default: 1, preserves full bar/dock usage)
    speed = 12.0;        # Gesture sensitivity multiplier (default: 12.0)
  };
}
```

*(Note: `services.niriScrollbar` is also supported as a backwards-compatible alias).*

---

### 2. (Optional) Automatic uinput Permissions in NixOS (`configuration.nix`)

To enable smooth trackpad gesture emulation without manually configuring udev rules or groups:

```nix
{
  imports = [
    inputs.niri-scrollbar.nixosModules.default
  ];

  services.waylandScrollbar.enable = true;
}
```

---

## 💻 Manual / Non-Nix Usage

Run directly with Python:

```bash
# Attach directly to the top edge (on top of existing bar):
python3 wayland_scrollbar.py --position top --layer overlay --height 1

# Or attach directly to the bottom edge (on top of existing dock):
python3 wayland_scrollbar.py --position bottom --layer overlay --height 1
```

See [NON_NIX_GUIDE.md](./NON_NIX_GUIDE.md) for distro package prerequisites.

---

## 📄 License

Distributed under the MIT License.
