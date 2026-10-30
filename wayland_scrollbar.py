#!/usr/bin/env python3
"""
Wayland Scrollbar
An invisible edge drag bar for smooth workspace scrolling in Wayland compositors (Niri, Umbriel).
Attached directly to screen edges on top of existing layers (OVERLAY) with an ultra-thin 1px trigger,
ensuring it never impedes usage, clicks, or hover detection of underlying bars or docks.
"""

import os
import sys
import argparse
import shutil
import subprocess
import threading

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell


# ─── Virtual Touchpad (uinput) ────────────────────────────────────────────────

class VirtualTouchpad:
    """Emulates multi-touch swipe gestures to replicate native trackpad smooth scrolling.
    Communicates via /dev/uinput. If restricted, gracefully falls back without crashing.
    """

    def __init__(self, speed=12.0):
        self.available = False
        self.ui = None
        self.e = None
        self.speed = speed
        # Wide coordinate baseline (30000) allowing huge drag range without out-of-bounds resets
        self.BASE_X = [30000, 32000, 34000]
        self.BASE_Y = [30000, 30000, 30000]
        self.finger_x = list(self.BASE_X)
        self.finger_y = list(self.BASE_Y)
        self.gesture_active = False
        self.lock = threading.Lock()

        try:
            from evdev import UInput, AbsInfo, ecodes as e
            self.e = e
            cap = {
                e.EV_KEY: [
                    e.BTN_LEFT,
                    e.BTN_TOUCH,
                    e.BTN_TOOL_FINGER,
                    e.BTN_TOOL_DOUBLETAP,
                    e.BTN_TOOL_TRIPLETAP,
                ],
                e.EV_ABS: [
                    (e.ABS_X,              AbsInfo(32000, 0, 100000, 0, 0, 40)),
                    (e.ABS_Y,              AbsInfo(30000, 0, 100000, 0, 0, 40)),
                    (e.ABS_MT_SLOT,        AbsInfo(0, 0, 4, 0, 0, 0)),
                    (e.ABS_MT_TRACKING_ID, AbsInfo(-1, -1, 65535, 0, 0, 0)),
                    (e.ABS_MT_POSITION_X,  AbsInfo(32000, 0, 100000, 0, 0, 40)),
                    (e.ABS_MT_POSITION_Y,  AbsInfo(30000, 0, 100000, 0, 0, 40)),
                ],
                e.EV_SYN: [],
            }
            self.ui = UInput(
                cap,
                name="virtual-touchpad",
                input_props=[e.INPUT_PROP_POINTER, e.INPUT_PROP_BUTTONPAD]
            )
            self.available = True
            print("[wayland-scrollbar] Virtual touchpad initialized successfully.")
        except Exception as err:
            self.available = False
            print(f"[wayland-scrollbar] Notice: /dev/uinput not available ({err}).")
            print("[wayland-scrollbar] Smooth gesture emulation disabled; using compositor IPC fallback.")

    def fingers_down(self):
        if not self.available:
            return
        with self.lock:
            e = self.e
            self.finger_x = list(self.BASE_X)
            self.finger_y = list(self.BASE_Y)
            for slot, (x, y, tid) in enumerate(zip(self.finger_x, self.finger_y, [10, 11, 12])):
                self.ui.write(e.EV_ABS, e.ABS_MT_SLOT, slot)
                self.ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, tid)
                self.ui.write(e.EV_ABS, e.ABS_MT_POSITION_X, x)
                self.ui.write(e.EV_ABS, e.ABS_MT_POSITION_Y, y)
            self.ui.write(e.EV_KEY, e.BTN_TOUCH, 1)
            self.ui.write(e.EV_KEY, e.BTN_TOOL_TRIPLETAP, 1)
            self.ui.write(e.EV_ABS, e.ABS_X, self.finger_x[1])
            self.ui.write(e.EV_ABS, e.ABS_Y, self.finger_y[1])
            self.ui.syn()
            self.gesture_active = True

    def fingers_move(self, dx, dy=0):
        if not self.available:
            return
        with self.lock:
            e = self.e
            self.finger_x = [x + dx for x in self.finger_x]
            self.finger_y = [y + dy for y in self.finger_y]
            for slot, (x, y) in enumerate(zip(self.finger_x, self.finger_y)):
                self.ui.write(e.EV_ABS, e.ABS_MT_SLOT, slot)
                self.ui.write(e.EV_ABS, e.ABS_MT_POSITION_X, x)
                self.ui.write(e.EV_ABS, e.ABS_MT_POSITION_Y, y)
            self.ui.write(e.EV_ABS, e.ABS_X, self.finger_x[1])
            self.ui.write(e.EV_ABS, e.ABS_Y, self.finger_y[1])
            self.ui.syn()

    def fingers_up(self):
        if not self.available:
            return
        with self.lock:
            if self.gesture_active:
                e = self.e
                for slot in range(3):
                    self.ui.write(e.EV_ABS, e.ABS_MT_SLOT, slot)
                    self.ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, -1)
                self.ui.write(e.EV_KEY, e.BTN_TOUCH, 0)
                self.ui.write(e.EV_KEY, e.BTN_TOOL_TRIPLETAP, 0)
                self.ui.syn()
                self.gesture_active = False

    def close(self):
        if self.available and self.ui:
            self.fingers_up()
            self.ui.close()


# ─── Compositor Adapter (Fallback) ────────────────────────────────────────────

class Compositor:
    """Provides discrete navigation fallback if uinput is not available."""

    def __init__(self):
        self.kind = self.detect()
        print(f"[wayland-scrollbar] Detected compositor environment: {self.kind}")

    def detect(self):
        if os.environ.get("UMBRIEL_SOCKET") or shutil.which("umbriel"):
            return "umbriel"
        if os.environ.get("NIRI_SOCKET") or shutil.which("niri"):
            return "niri"
        return "auto"

    def action(self, act):
        try:
            if self.kind == "umbriel" or shutil.which("umbriel"):
                umbriel_map = {
                    "focus-left": ["umbriel", "msg", "column-focus-previous"],
                    "focus-right": ["umbriel", "msg", "column-focus-next"],
                    "workspace-up": ["umbriel", "msg", "workspace-focus-up"],
                    "workspace-down": ["umbriel", "msg", "workspace-focus-down"],
                }
                cmd = umbriel_map.get(act)
                if cmd:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
            if self.kind == "niri" or shutil.which("niri"):
                niri_map = {
                    "focus-left": ["niri", "msg", "action", "focus-column-left"],
                    "focus-right": ["niri", "msg", "action", "focus-column-right"],
                    "workspace-up": ["niri", "msg", "action", "focus-workspace-up"],
                    "workspace-down": ["niri", "msg", "action", "focus-workspace-down"],
                }
                cmd = niri_map.get(act)
                if cmd:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[wayland-scrollbar] Action error: {e}")


# ─── Invisible Layer Window ───────────────────────────────────────────────────

class InvisibleBarWindow(Gtk.Window):
    def __init__(self, monitor, touchpad, compositor, position="top", layer="overlay", height=1, speed=12.0):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.monitor = monitor
        self.touchpad = touchpad
        self.compositor = compositor
        self.position = position.lower()
        self.layer_mode = layer.lower()
        self.bar_height = max(1, height)
        self.speed = speed

        self.last_drag_x = 0
        self.last_drag_y = 0
        self.accumulated_dx = 0
        self.accumulated_dy = 0
        self.is_dragging = False

        self._setup_layer_shell()
        self._build_ui()

    def _setup_layer_shell(self):
        GtkLayerShell.init_for_window(self)

        # Place on OVERLAY layer so it sits above the bar/dock on TOP layer
        if self.layer_mode == "top":
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        else:
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)

        # Attached directly to screen edge without offset
        if self.position == "bottom":
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, False)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        elif self.position == "left":
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, False)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        elif self.position == "right":
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, False)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        else:  # top (default)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, False)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        GtkLayerShell.set_namespace(self, "wayland-scrollbar")
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        # 0 exclusive zone so windows are never displaced
        GtkLayerShell.set_exclusive_zone(self, 0)

        if self.monitor:
            GtkLayerShell.set_monitor(self, self.monitor)

    def _build_ui(self):
        self.hit_zone = Gtk.EventBox()
        self.hit_zone.set_visible(True)

        if self.position in ("left", "right"):
            self.hit_zone.set_size_request(self.bar_height, -1)
            self.hit_zone.set_hexpand(False)
            self.hit_zone.set_vexpand(True)
        else:
            self.hit_zone.set_size_request(-1, self.bar_height)
            self.hit_zone.set_hexpand(True)
            self.hit_zone.set_vexpand(False)

        self.hit_zone.get_style_context().add_class("invisible-drag-bar")

        self.hit_zone.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK
        )

        self.hit_zone.connect("scroll-event", self._on_scroll)
        self.add(self.hit_zone)

        # Drag gesture (left mouse button)
        self.drag = Gtk.GestureDrag.new(self.hit_zone)
        self.drag.set_button(1)
        self.drag.connect("drag-begin", self._on_drag_begin)
        self.drag.connect("drag-update", self._on_drag_update)
        self.drag.connect("drag-end", self._on_drag_end)

        self._drag = self.drag

    def _on_scroll(self, _widget, event):
        """Mouse wheel scrolling on edge scrolls columns."""
        if event.direction == Gdk.ScrollDirection.UP or event.delta_y < 0 or event.delta_x < 0:
            if self.touchpad.available:
                self.touchpad.fingers_down()
                self.touchpad.fingers_move(-120, 0)
                self.touchpad.fingers_up()
            else:
                self.compositor.action("focus-left")
            return True
        elif event.direction == Gdk.ScrollDirection.DOWN or event.delta_y > 0 or event.delta_x > 0:
            if self.touchpad.available:
                self.touchpad.fingers_down()
                self.touchpad.fingers_move(120, 0)
                self.touchpad.fingers_up()
            else:
                self.compositor.action("focus-right")
            return True
        return False

    def _on_drag_begin(self, _gesture, _start_x, _start_y):
        self.last_drag_x = 0
        self.last_drag_y = 0
        self.accumulated_dx = 0
        self.accumulated_dy = 0
        self.is_dragging = True
        self.touchpad.fingers_down()

    def _on_drag_update(self, _gesture, offset_x, offset_y):
        if not self.is_dragging:
            return

        dx = offset_x - self.last_drag_x
        dy = offset_y - self.last_drag_y
        self.last_drag_x = offset_x
        self.last_drag_y = offset_y

        # If on left/right edges, vertical motion naturally translates to ribbon scroll
        if self.position in ("left", "right"):
            effective_dx = dx if abs(dx) > abs(dy) else dy
            effective_dy = 0
        else:
            effective_dx = dx
            effective_dy = dy

        if self.touchpad.available:
            scaled_dx = int(round(effective_dx * self.speed))
            scaled_dy = int(round(effective_dy * self.speed))
            self.touchpad.fingers_move(scaled_dx, scaled_dy)
        else:
            self.accumulated_dx += effective_dx
            self.accumulated_dy += effective_dy
            threshold = 28

            if self.accumulated_dx >= threshold:
                self.compositor.action("focus-right")
                self.accumulated_dx = 0
            elif self.accumulated_dx <= -threshold:
                self.compositor.action("focus-left")
                self.accumulated_dx = 0

            if self.accumulated_dy >= threshold:
                self.compositor.action("workspace-down")
                self.accumulated_dy = 0
            elif self.accumulated_dy <= -threshold:
                self.compositor.action("workspace-up")
                self.accumulated_dy = 0

    def _on_drag_end(self, _gesture, _offset_x, _offset_y):
        if self.is_dragging:
            self.touchpad.fingers_up()
            self.is_dragging = False


# ─── Application Orchestrator ─────────────────────────────────────────────────

class Application:
    def __init__(self, position="top", layer="overlay", height=1, speed=12.0):
        self.position = position.lower()
        self.layer = layer.lower()
        self.height = max(1, height)
        self.speed = speed
        self.touchpad = VirtualTouchpad(speed=speed)
        self.compositor = Compositor()
        self.windows = []
        self.display = Gdk.Display.get_default()

        print(f"[wayland-scrollbar] Position: {self.position}, Layer: {self.layer}, Trigger thickness: {self.height}px")

        self._apply_styles()
        self._setup_monitors()

        if self.display:
            self.display.connect("monitor-added", lambda *_: self._setup_monitors())
            self.display.connect("monitor-removed", lambda *_: self._setup_monitors())

    def _apply_styles(self):
        css = """
        window {
            background-color: transparent;
        }
        .invisible-drag-bar {
            background-color: rgba(0, 0, 0, 0.005);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _setup_monitors(self):
        for win in self.windows:
            win.destroy()
        self.windows.clear()

        if not self.display:
            return

        n = self.display.get_n_monitors()
        for i in range(n):
            mon = self.display.get_monitor(i)
            win = InvisibleBarWindow(
                monitor=mon,
                touchpad=self.touchpad,
                compositor=self.compositor,
                position=self.position,
                layer=self.layer,
                height=self.height,
                speed=self.speed
            )
            self.windows.append(win)
            win.show_all()


def main():
    parser = argparse.ArgumentParser(
        description="Invisible edge drag bar for smooth workspace scrolling in Wayland compositors (Niri, Umbriel)"
    )
    parser.add_argument(
        "--position",
        choices=["top", "bottom", "left", "right"],
        default=os.environ.get("SCROLLBAR_POSITION", "top").lower(),
        help="Screen edge to attach the drag bar to: 'top', 'bottom', 'left', or 'right' (default: top)"
    )
    parser.add_argument(
        "--layer",
        choices=["overlay", "top"],
        default=os.environ.get("SCROLLBAR_LAYER", "overlay").lower(),
        help="Layer to place the scrollbar on: 'overlay' (on top of existing bar/dock) or 'top' (default: overlay)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=int(os.environ.get("SCROLLBAR_HEIGHT", 1)),
        help="Trigger thickness in pixels at the screen edge (default: 1, preserves full usage and hover detection of bar/dock below)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=float(os.environ.get("SCROLLBAR_SPEED", 12.0)),
        help="Gesture scrolling speed multiplier (default: 12.0)"
    )
    args = parser.parse_args()

    app = Application(
        position=args.position,
        layer=args.layer,
        height=args.height,
        speed=args.speed
    )
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        app.touchpad.close()


if __name__ == "__main__":
    main()
