# Running on Non-NixOS Distributions 🐧

If you are not using Nix Flakes or NixOS, you can run the invisible scrollbar directly using Python.

## 📋 Prerequisites

Ensure you have the following installed on your system:

1. **Python 3** (with `python3-pip`)
2. **GTK 3** and **GTK Layer Shell**:
   - **Arch Linux**: `sudo pacman -S gtk3 gtk-layer-shell python-gobject python-evdev`
   - **Fedora**: `sudo dnf install gtk3 gtk-layer-shell python3-gobject python3-evdev`
   - **Ubuntu/Debian**: `sudo apt install libgtk-3-0 libgtk-layer-shell0 python3-gi python3-evdev gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1`
3. A running Wayland compositor (**Niri** or **Umbriel**).

---

## 🚀 Running Directly

Run the script:

```bash
# Attach right below your top bar (auto-detected thickness)
python3 wayland_scrollbar.py --position top --offset auto

# Or attach on left screen edge to completely avoid top bar and bottom dock
python3 wayland_scrollbar.py --position left

# Or manually specify an offset (e.g. 34px below the top edge)
python3 wayland_scrollbar.py --position top --offset 34
```

The script will:
1. Connect to the display and automatically detect your compositor and shell elements (e.g. Noctalia bar/dock).
2. Attach an invisible drag strip on layer `TOP`, offset so it never conflicts with your bar buttons or dock icons.
3. Check if `/dev/uinput` is writable:
   - If accessible: creates a virtual touchpad and provides smooth 3-finger trackpad scrolling when clicking & dragging.
   - If restricted: logs a note and falls back to compositor IPC column navigation—no crashes!

---

## ⚙️ (Optional) Enabling Smooth Gesture Emulation

If you want smooth hardware gesture emulation instead of discrete IPC scrolling, grant access to `/dev/uinput`:

1. Add your user to the `input` group:
   ```bash
   sudo usermod -aG input $USER
   ```
2. Create `/etc/udev/rules.d/99-uinput.rules`:
   ```text
   KERNEL=="uinput", GROUP="input", MODE="0660", TAG+="uaccess"
   ```
3. Reload udev rules:
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
   (or log out and log back in).

---

## 🔄 Systemd User Service

To start the scrollbar automatically on login:

Create `~/.config/systemd/user/wayland-scrollbar.service`:

```ini
[Unit]
Description=Wayland Invisible Scrollbar
PartOf=graphical-session.target
After=graphical-session.target

[Service]
ExecStart=/usr/bin/python3 /path/to/wayland_scrollbar.py --position top --offset auto
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable --now wayland-scrollbar.service
```
