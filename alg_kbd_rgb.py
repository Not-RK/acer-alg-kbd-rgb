#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Cross-distro GUI & CLI for Acer ALG AL15G-52 (Clevo WMI) RGB Keyboard Backlight."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LED_DIR = Path("/sys/class/leds/rgb:kbd_backlight")
INTENSITY_PATH = LED_DIR / "multi_intensity"
BRIGHTNESS_PATH = LED_DIR / "brightness"
MAX_BRIGHTNESS_PATH = LED_DIR / "max_brightness"
CONFIG_PATH = Path.home() / ".config" / "alg-kbd-rgb.json"

PRESETS = [
    ("Blue (Default)", 0, 0, 255),
    ("Ice Blue", 0, 160, 255),
    ("Cyan", 0, 255, 255),
    ("Red", 255, 0, 0),
    ("Green", 0, 255, 0),
    ("Yellow", 255, 220, 0),
    ("Orange", 255, 90, 0),
    ("Purple", 160, 0, 255),
    ("Pink", 255, 0, 150),
    ("White", 255, 255, 255),
]


def clamp_u8(val: int) -> int:
    return max(0, min(255, int(val)))


def read_int(path: Path, default: int) -> int:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return default


def read_rgb() -> tuple[int, int, int]:
    try:
        parts = INTENSITY_PATH.read_text().strip().split()
        if len(parts) == 3:
            return tuple(clamp_u8(int(x)) for x in parts)
    except (OSError, ValueError):
        pass
    return (0, 0, 255)


def set_upower_brightness(value: int) -> bool:
    for cmd in (
        [
            "gdbus",
            "call",
            "--system",
            "--dest",
            "org.freedesktop.UPower",
            "--object-path",
            "/org/freedesktop/UPower/KbdBacklight",
            "--method",
            "org.freedesktop.UPower.KbdBacklight.SetBrightness",
            str(value),
        ],
        [
            "dbus-send",
            "--system",
            "--type=method_call",
            "--dest=org.freedesktop.UPower",
            "/org/freedesktop/UPower/KbdBacklight",
            "org.freedesktop.UPower.KbdBacklight.SetBrightness",
            f"int32:{value}",
        ],
    ):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def apply_hw_rgb_brightness(r: int, g: int, b: int, brightness: int) -> tuple[bool, str]:
    """Write RGB intensity and trigger brightness update so kernel applies color."""
    r, g, b = clamp_u8(r), clamp_u8(g), clamp_u8(b)
    max_b = read_int(MAX_BRIGHTNESS_PATH, 255)
    brightness = max(0, min(max_b, int(brightness)))

    if not LED_DIR.exists():
        return False, f"LED interface not found: {LED_DIR} (load tuxedo_keyboard & clevo_wmi)"

    try:
        INTENSITY_PATH.write_text(f"{r} {g} {b}\n")
    except PermissionError:
        return (
            False,
            f"Permission denied writing {INTENSITY_PATH}. Run install.sh once to set udev permissions.",
        )
    except OSError as exc:
        return False, f"Failed writing {INTENSITY_PATH}: {exc}"

    try:
        BRIGHTNESS_PATH.write_text(f"{brightness}\n")
    except PermissionError:
        if not set_upower_brightness(brightness):
            return False, f"Permission denied writing {BRIGHTNESS_PATH}."
    except OSError as exc:
        return False, f"Failed writing {BRIGHTNESS_PATH}: {exc}"

    return True, ""


def load_config() -> dict:
    try:
        data = json.loads(CONFIG_PATH.read_text())
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_config(r: int, g: int, b: int, brightness: int) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps({"r": r, "g": g, "b": b, "brightness": brightness}, indent=2)
        )
    except OSError:
        pass


def initial_state() -> tuple[tuple[int, int, int], int, int]:
    max_b = max(1, read_int(MAX_BRIGHTNESS_PATH, 255))
    cfg = load_config()
    hw_r, hw_g, hw_blue = read_rgb()
    hw_bright = read_int(BRIGHTNESS_PATH, max_b)
    rgb = (
        clamp_u8(cfg.get("r", hw_r)),
        clamp_u8(cfg.get("g", hw_g)),
        clamp_u8(cfg.get("b", hw_blue)),
    )
    return rgb, max(0, min(max_b, hw_bright)), max_b


def _import_qt():
    """Import PySide6, PyQt6, or PyQt5 transparently."""
    for mod_name in ("PySide6", "PyQt6", "PyQt5"):
        try:
            pkg = __import__(mod_name, fromlist=["QtCore", "QtGui", "QtWidgets"])
            return mod_name, pkg.QtCore, pkg.QtGui, pkg.QtWidgets
        except ImportError:
            continue
    return None


def _qt_enum(obj, scoped_attr: str, legacy_attr: str):
    cur = obj
    for part in scoped_attr.split("."):
        if not hasattr(cur, part):
            return getattr(obj, legacy_attr)
        cur = getattr(cur, part)
    return cur


def run_qt_gui() -> int:
    loaded = _import_qt()
    if loaded is None:
        raise ImportError("No Qt bindings found")
    _name, QtCore, QtGui, QtWidgets = loaded

    class KbdRgbWindow(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Acer ALG Keyboard RGB")
            self.setMinimumWidth(420)

            self.rgb, self.brightness, self.max_brightness = initial_state()
            self._build_ui()
            self._refresh_preview()

            self._poll_timer = QtCore.QTimer(self)
            self._poll_timer.setInterval(800)
            self._poll_timer.timeout.connect(self._sync_from_sysfs)
            self._poll_timer.start()

        def _build_ui(self) -> None:
            root = QtWidgets.QVBoxLayout(self)
            root.setSpacing(14)
            root.setContentsMargins(18, 18, 18, 18)

            header = QtWidgets.QHBoxLayout()
            title_box = QtWidgets.QVBoxLayout()
            title = QtWidgets.QLabel("Acer ALG AL15G-52 Keyboard RGB")
            title_font = title.font()
            title_font.setPointSize(13)
            title_font.setBold(True)
            title.setFont(title_font)
            subtitle = QtWidgets.QLabel("Fn+* toggles ON/OFF  |  Fn+- / Fn++ adjusts brightness")
            subtitle.setStyleSheet("color: gray; font-size: 11px;")
            title_box.addWidget(title)
            title_box.addWidget(subtitle)

            self.preview_box = QtWidgets.QFrame()
            self.preview_box.setFixedSize(48, 48)
            self.preview_box.setFrameShape(
                _qt_enum(QtWidgets.QFrame, "Shape.StyledPanel", "StyledPanel")
            )
            header.addLayout(title_box)
            header.addStretch()
            header.addWidget(self.preview_box)
            root.addLayout(header)

            presets_group = QtWidgets.QGroupBox("Quick Colors")
            grid = QtWidgets.QGridLayout(presets_group)
            grid.setSpacing(8)
            for idx, (label, r, g, b) in enumerate(PRESETS):
                btn = QtWidgets.QPushButton(label)
                btn.setMinimumHeight(34)
                btn.setIcon(self._swatch_icon(r, g, b))
                btn.setIconSize(QtCore.QSize(16, 16))
                btn.clicked.connect(lambda _=False, col=(r, g, b): self._on_pick_color(*col))
                grid.addWidget(btn, idx // 2, idx % 2)
            root.addWidget(presets_group)

            pick_btn = QtWidgets.QPushButton("Custom Color Picker...")
            pick_btn.setMinimumHeight(38)
            pick_btn.clicked.connect(self._open_color_dialog)
            root.addWidget(pick_btn)

            bright_group = QtWidgets.QGroupBox("Brightness")
            bright_layout = QtWidgets.QVBoxLayout(bright_group)

            slider_row = QtWidgets.QHBoxLayout()
            self.slider = QtWidgets.QSlider(
                _qt_enum(QtCore.Qt, "Orientation.Horizontal", "Horizontal")
            )
            self.slider.setRange(0, self.max_brightness)
            self.slider.setValue(self.brightness)
            self.slider.valueChanged.connect(self._on_slider_changed)

            self.bright_label = QtWidgets.QLabel()
            self.bright_label.setMinimumWidth(48)
            align_r = _qt_enum(QtCore.Qt, "AlignmentFlag.AlignRight", "AlignRight")
            align_v = _qt_enum(QtCore.Qt, "AlignmentFlag.AlignVCenter", "AlignVCenter")
            self.bright_label.setAlignment(align_r | align_v)

            slider_row.addWidget(self.slider)
            slider_row.addWidget(self.bright_label)
            bright_layout.addLayout(slider_row)

            btn_row = QtWidgets.QHBoxLayout()
            off_btn = QtWidgets.QPushButton("Off (0%)")
            off_btn.clicked.connect(lambda: self.slider.setValue(0))
            mid_btn = QtWidgets.QPushButton("50%")
            mid_btn.clicked.connect(lambda: self.slider.setValue(self.max_brightness // 2))
            max_btn = QtWidgets.QPushButton("Max (100%)")
            max_btn.clicked.connect(lambda: self.slider.setValue(self.max_brightness))
            btn_row.addWidget(off_btn)
            btn_row.addWidget(mid_btn)
            btn_row.addWidget(max_btn)
            bright_layout.addLayout(btn_row)
            root.addWidget(bright_group)

            self.status_label = QtWidgets.QLabel()
            self.status_label.setWordWrap(True)
            self.status_label.setStyleSheet("font-size: 11px;")
            root.addWidget(self.status_label)

            if not LED_DIR.exists():
                self.status_label.setText(
                    "Warning: /sys/class/leds/rgb:kbd_backlight not found. Load tuxedo_keyboard & clevo_wmi."
                )
                self.status_label.setStyleSheet("color: #d9534f; font-size: 11px;")
            elif not os.access(INTENSITY_PATH, os.W_OK):
                self.status_label.setText(
                    "Note: Run install.sh once so colors apply without sudo."
                )
                self.status_label.setStyleSheet("color: #f0ad4e; font-size: 11px;")

        @staticmethod
        def _swatch_icon(r: int, g: int, b: int):
            pix = QtGui.QPixmap(16, 16)
            pix.fill(QtGui.QColor(r, g, b))
            painter = QtGui.QPainter(pix)
            painter.setPen(QtGui.QColor(80, 80, 80))
            painter.drawRect(0, 0, 15, 15)
            painter.end()
            return QtGui.QIcon(pix)

        def _refresh_preview(self) -> None:
            r, g, b = self.rgb
            self.preview_box.setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); border: 1px solid #666; border-radius: 6px;"
            )
            pct = round((self.brightness / max(1, self.max_brightness)) * 100)
            self.bright_label.setText(f"{pct}%")

        def _apply_current(self) -> None:
            r, g, b = self.rgb
            ok, err = apply_hw_rgb_brightness(r, g, b, self.brightness)
            if ok:
                save_config(r, g, b, self.brightness)
                pct = round(self.brightness * 100 / self.max_brightness)
                self.status_label.setText(f"Applied RGB({r}, {g}, {b}) at {pct}%")
                self.status_label.setStyleSheet("color: #5cb85c; font-size: 11px;")
            else:
                self.status_label.setText(err)
                self.status_label.setStyleSheet("color: #d9534f; font-size: 11px;")
            self._refresh_preview()

        def _on_pick_color(self, r: int, g: int, b: int) -> None:
            self.rgb = (r, g, b)
            if self.brightness == 0:
                self.brightness = self.max_brightness
                self.slider.blockSignals(True)
                self.slider.setValue(self.brightness)
                self.slider.blockSignals(False)
            self._apply_current()

        def _open_color_dialog(self) -> None:
            initial = QtGui.QColor(*self.rgb)
            dlg = QtWidgets.QColorDialog(initial, self)
            dlg.setOption(
                _qt_enum(
                    QtWidgets.QColorDialog,
                    "ColorDialogOption.DontUseNativeDialog",
                    "DontUseNativeDialog",
                ),
                True,
            )
            dlg.currentColorChanged.connect(
                lambda c: self._on_pick_color(c.red(), c.green(), c.blue()) if c.isValid() else None
            )
            accepted = _qt_enum(QtWidgets.QDialog, "DialogCode.Accepted", "Accepted")
            exec_fn = getattr(dlg, "exec", None) or getattr(dlg, "exec_")
            if exec_fn() == accepted:
                c = dlg.selectedColor()
                if c.isValid():
                    self._on_pick_color(c.red(), c.green(), c.blue())

        def _on_slider_changed(self, value: int) -> None:
            self.brightness = value
            self._apply_current()

        def _sync_from_sysfs(self) -> None:
            hw_bright = read_int(BRIGHTNESS_PATH, self.brightness)
            if hw_bright != self.brightness:
                self.brightness = hw_bright
                self.slider.blockSignals(True)
                self.slider.setValue(hw_bright)
                self.slider.blockSignals(False)
                self._refresh_preview()

    app = QtWidgets.QApplication(sys.argv)
    win = KbdRgbWindow()
    win.show()
    exec_fn = getattr(app, "exec", None) or getattr(app, "exec_")
    return int(exec_fn())


def run_tk_gui() -> int:
    import tkinter as tk
    from tkinter import colorchooser, ttk

    root = tk.Tk()
    root.title("Acer ALG Keyboard RGB")
    root.resizable(False, False)

    state_rgb, state_bright, max_b = initial_state()
    state = {"rgb": state_rgb, "brightness": state_bright, "syncing": False}

    main_frame = ttk.Frame(root, padding=16)
    main_frame.pack(fill="both", expand=True)

    header = ttk.Frame(main_frame)
    header.pack(fill="x", pady=(0, 12))

    titles = ttk.Frame(header)
    titles.pack(side="left", fill="x", expand=True)
    ttk.Label(
        titles, text="Acer ALG AL15G-52 Keyboard RGB", font=("Sans", 12, "bold")
    ).pack(anchor="w")
    ttk.Label(
        titles, text="Fn+* toggles ON/OFF  |  Fn+- / Fn++ adjusts brightness", foreground="gray"
    ).pack(anchor="w")

    preview = tk.Frame(header, width=44, height=44, relief="solid", borderwidth=1)
    preview.pack(side="right", padx=(12, 0))
    preview.pack_propagate(False)

    presets_box = ttk.LabelFrame(main_frame, text="Quick Colors", padding=10)
    presets_box.pack(fill="x", pady=(0, 10))
    presets_box.columnconfigure(0, weight=1)
    presets_box.columnconfigure(1, weight=1)

    status_var = tk.StringVar(value="")
    bright_var = tk.IntVar(value=state["brightness"])
    pct_var = tk.StringVar(value=f"{round(state['brightness'] * 100 / max_b)}%")

    def refresh_preview() -> None:
        r, g, b = state["rgb"]
        preview.configure(bg=f"#{r:02x}{g:02x}{b:02x}")
        pct_var.set(f"{round(state['brightness'] * 100 / max_b)}%")

    def apply_current() -> None:
        r, g, b = state["rgb"]
        ok, err = apply_hw_rgb_brightness(r, g, b, state["brightness"])
        if ok:
            save_config(r, g, b, state["brightness"])
            pct = round(state["brightness"] * 100 / max_b)
            status_var.set(f"Applied RGB({r}, {g}, {b}) at {pct}%")
            status_lbl.configure(foreground="#2e8b57")
        else:
            status_var.set(err)
            status_lbl.configure(foreground="#c9302c")
        refresh_preview()

    def pick_color(r: int, g: int, b: int) -> None:
        state["rgb"] = (r, g, b)
        if state["brightness"] == 0:
            state["brightness"] = max_b
            state["syncing"] = True
            bright_var.set(max_b)
            state["syncing"] = False
        apply_current()

    for idx, (label, r, g, b) in enumerate(PRESETS):
        cell = ttk.Frame(presets_box)
        cell.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=4, pady=3)
        swatch = tk.Label(cell, width=2, bg=f"#{r:02x}{g:02x}{b:02x}", relief="solid", bd=1)
        swatch.pack(side="left", padx=(0, 6))
        btn = ttk.Button(cell, text=label, command=lambda c=(r, g, b): pick_color(*c))
        btn.pack(side="left", fill="x", expand=True)

    def open_picker() -> None:
        r, g, b = state["rgb"]
        chosen, _hex = colorchooser.askcolor(color=f"#{r:02x}{g:02x}{b:02x}", parent=root)
        if chosen is not None:
            pick_color(int(chosen[0]), int(chosen[1]), int(chosen[2]))

    ttk.Button(main_frame, text="Custom Color Picker...", command=open_picker).pack(
        fill="x", pady=(0, 10)
    )

    bright_box = ttk.LabelFrame(main_frame, text="Brightness", padding=10)
    bright_box.pack(fill="x", pady=(0, 10))

    def on_slide(val_str: str) -> None:
        if state["syncing"]:
            return
        state["brightness"] = int(float(val_str))
        apply_current()

    slider_row = ttk.Frame(bright_box)
    slider_row.pack(fill="x")
    scale = ttk.Scale(
        slider_row, from_=0, to=max_b, variable=bright_var, command=on_slide
    )
    scale.pack(side="left", fill="x", expand=True)
    ttk.Label(slider_row, textvariable=pct_var, width=5, anchor="e").pack(side="right")

    def set_level(val: int) -> None:
        bright_var.set(val)
        state["brightness"] = val
        apply_current()

    btn_row = ttk.Frame(bright_box)
    btn_row.pack(fill="x", pady=(8, 0))
    ttk.Button(btn_row, text="Off (0%)", command=lambda: set_level(0)).pack(
        side="left", expand=True, fill="x", padx=2
    )
    ttk.Button(btn_row, text="50%", command=lambda: set_level(max_b // 2)).pack(
        side="left", expand=True, fill="x", padx=2
    )
    ttk.Button(btn_row, text="Max (100%)", command=lambda: set_level(max_b)).pack(
        side="left", expand=True, fill="x", padx=2
    )

    status_lbl = ttk.Label(main_frame, textvariable=status_var, wraplength=380)
    status_lbl.pack(fill="x")

    if not LED_DIR.exists():
        status_var.set("Warning: /sys/class/leds/rgb:kbd_backlight not found.")
        status_lbl.configure(foreground="#c9302c")
    elif not os.access(INTENSITY_PATH, os.W_OK):
        status_var.set("Note: Run install.sh once so colors apply without sudo.")
        status_lbl.configure(foreground="#b87503")

    refresh_preview()

    def poll_sysfs() -> None:
        hw_b = read_int(BRIGHTNESS_PATH, state["brightness"])
        if hw_b != state["brightness"]:
            state["brightness"] = hw_b
            state["syncing"] = True
            bright_var.set(hw_b)
            state["syncing"] = False
            refresh_preview()
        root.after(800, poll_sysfs)

    root.after(800, poll_sysfs)
    root.mainloop()
    return 0


def restore_saved() -> int:
    cfg = load_config()
    r = clamp_u8(cfg.get("r", 0))
    g = clamp_u8(cfg.get("g", 0))
    b = clamp_u8(cfg.get("b", 255))
    max_b = read_int(MAX_BRIGHTNESS_PATH, 255)
    brightness = max(0, min(max_b, int(cfg.get("brightness", max_b))))
    ok, err = apply_hw_rgb_brightness(r, g, b, brightness)
    if not ok:
        print(err, file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acer ALG AL15G-52 Keyboard RGB GUI & CLI"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Apply saved color & brightness without opening GUI",
    )
    parser.add_argument(
        "--set",
        nargs=3,
        type=int,
        metavar=("R", "G", "B"),
        help="Set RGB color (0-255 each) from CLI",
    )
    parser.add_argument(
        "--brightness",
        type=int,
        metavar="N",
        help="Set brightness (0-255) from CLI",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current hardware RGB/brightness and exit",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "qt", "tk"),
        default="auto",
        help="GUI toolkit backend (default: auto)",
    )
    args = parser.parse_args()

    if args.status:
        rgb = read_rgb()
        max_b = read_int(MAX_BRIGHTNESS_PATH, 255)
        cur_b = read_int(BRIGHTNESS_PATH, -1)
        print(
            json.dumps(
                {
                    "led_exists": LED_DIR.exists(),
                    "writable": os.access(INTENSITY_PATH, os.W_OK),
                    "rgb": list(rgb),
                    "brightness": cur_b,
                    "max_brightness": max_b,
                    "saved": load_config(),
                },
                indent=2,
            )
        )
        return 0

    if args.restore:
        return restore_saved()

    if args.set is not None or args.brightness is not None:
        rgb, cur_b, max_b = initial_state()
        r, g, b = args.set if args.set is not None else rgb
        brightness = args.brightness if args.brightness is not None else (cur_b or max_b)
        ok, err = apply_hw_rgb_brightness(r, g, b, brightness)
        if not ok:
            print(err, file=sys.stderr)
            return 1
        save_config(clamp_u8(r), clamp_u8(g), clamp_u8(b), brightness)
        return 0

    if args.backend in ("auto", "qt"):
        try:
            return run_qt_gui()
        except ImportError:
            if args.backend == "qt":
                print(
                    "No Qt Python binding installed (PySide6, PyQt6, or PyQt5).",
                    file=sys.stderr,
                )
                return 1

    try:
        return run_tk_gui()
    except ImportError:
        print(
            "No GUI toolkit found. Install one of:\n"
            "  Fedora:        sudo dnf install python3-pyside6 (or python3-tkinter)\n"
            "  Ubuntu/Debian: sudo apt install python3-pyqt5 (or python3-tk)\n"
            "  Arch Linux:    sudo pacman -S pyside6 (or tk)\n"
            "  openSUSE:      sudo zypper install python3-qt5 (or python3-tk)",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
