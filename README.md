# Wayland Scrollbar 🖱️

An **invisible edge drag bar** for scrolling Wayland compositors (such as **Niri** and **Umbriel**).

Attached to any screen edge (**top**, **bottom**, **left**, or **right**) on the **`TOP` layer** (not overlay), it lets you click and drag anywhere along the edge to smoothly scroll workspaces and columns—functioning identically to native trackpad 3-finger swipe gestures.

---

## ✨ Features

- **Completely Invisible**: Zero visual UI clutter—just a thin, transparent hit zone.
- **No Bar / Dock Collisions**:
  - **Auto-Offset**: Automatically detects top bar and bottom dock heights (e.g. from Noctalia) and offsets the drag bar so your bar buttons and dock icons remain 100% unimpeded.
  - **Manual Offset (`--offset <px>`)**: Manually position the drag strip right below your bar (e.g. `--offset 34`) or above your dock.
  - **Four Screen Edges (`top`, `bottom`, `left`, `right`)**: Place the drag bar along the left or right side of your screens to keep top and bottom entirely clear.
- **`TOP` Layer**: Runs on the Wayland `TOP` layer with `0` exclusive zone, ensuring it never displaces or shrinks normal windows.
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
    offset = "auto";     # "auto" (detects bar/dock height) or integer in pixels (e.g. 34)
    height = 10;         # Thickness in pixels of the hit zone (default: 10)
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
# Auto-offset beneath top bar (default)
python3 wayland_scrollbar.py --position top --offset auto

# Or place on left edge to avoid top bar and bottom dock completely:
python3 wayland_scrollbar.py --position left

# Or manually set offset below a 34px bar:
python3 wayland_scrollbar.py --position top --offset 34
```

See [NON_NIX_GUIDE.md](./NON_NIX_GUIDE.md) for distro package prerequisites.

---

## 📄 License

Distributed under the MIT License.
