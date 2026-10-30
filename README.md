# Wayland Scrollbar 🖱️

An **invisible edge drag bar** for scrolling Wayland compositors (such as **Niri** and **Umbriel**).

Attached seamlessly to the **top** or **bottom** of all monitors on the **`TOP` layer** (not overlay), it lets you click and drag anywhere along the screen edge to smoothly scroll workspaces and columns—functioning identically to native trackpad 3-finger swipe gestures.

---

## ✨ Features

- **Completely Invisible**: Zero visual UI clutter—just a thin, transparent hit zone at the edge of your monitors.
- **Top or Bottom Position**: Configure whether the scrollbar sits along the `top` or `bottom` edge of the screen.
- **`TOP` Layer**: Runs on the Wayland `TOP` layer with `0` exclusive zone, ensuring it never displaces or shrinks normal windows.
- **Smooth Trackpad Emulation**: Emulates hardware 3-finger swipe gestures via `/dev/uinput` for fluid, continuous scrolling in both Niri and Umbriel.
- **Graceful IPC Fallback**: If `/dev/uinput` permissions are not enabled, it automatically falls back to compositor IPC column navigation without crashing.
- **Multi-Monitor Native**: Spans across all active monitors and automatically updates when displays are connected or disconnected.
- **Mouse Wheel Support**: Rolling the scroll wheel at the edge also scrolls columns.
- **Customizable**: Adjust trigger edge (`top` / `bottom`), thickness in pixels (default: `10`), and speed sensitivity (default: `12.0`).

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
    position = "top";  # "top" or "bottom" (default: "top")
    height = 10;       # Height/thickness in pixels of the hit zone (default: 10)
    speed = 12.0;      # Gesture sensitivity multiplier (default: 12.0)
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
# Top edge (default)
python3 wayland_scrollbar.py --position top --height 10 --speed 12.0

# Bottom edge
python3 wayland_scrollbar.py --position bottom --height 10 --speed 12.0
```

See [NON_NIX_GUIDE.md](./NON_NIX_GUIDE.md) for distro package prerequisites.

---

## 📄 License

Distributed under the MIT License.
