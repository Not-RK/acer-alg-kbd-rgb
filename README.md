# Acer ALG AL15G-52 — Keyboard RGB & Backlight Fix for Linux

<p align="center">
  <img src="alg-kbd-rgb.svg" alt="alg-kbd-rgb icon" width="96"/>
</p>

<p align="center">
  <strong>Universal cross-distro Linux driver + GUI/CLI tool</strong><br>
  Fix broken Fn hotkeys &amp; get full RGB color control on the Acer ALG AL15G-52 (Clevo WMI platform).
</p>

<p align="center">
  <a href="#quick-install"><img alt="Quick Install" src="https://img.shields.io/badge/Install-1%20command-brightgreen?style=flat-square"/></a>
  <a href="https://github.com/tuxedocomputers/tuxedo-drivers"><img alt="Upstream: tuxedo-drivers v4.25.1" src="https://img.shields.io/badge/Upstream-tuxedo--drivers%20v4.25.1-blue?style=flat-square"/></a>
  <a href="LICENSE"><img alt="License: GPL-2.0-or-later" src="https://img.shields.io/badge/License-GPL--2.0--or--later-orange?style=flat-square"/></a>
</p>

> [!WARNING]
> **Disclaimer & "Vibe Coded" Notice:**  
> This project is **totally vibecoded**. It was cobbled together to fix issues on a specific machine and **may or may not work on your system**. Use it entirely at your own risk.  
> **I take absolutely no responsibility** if anything breaks, your system panics, your keyboard catches fire, or anything goes wrong. You have been warned!

---

## Table of Contents

- [What This Fixes](#what-this-fixes)
- [How It Works](#how-it-works)
- [Supported Distros](#supported-distros)
- [Quick Install](#quick-install)
- [Usage](#usage)
- [Uninstall](#uninstall)
- [Project Structure](#project-structure)
- [Credits & Upstream Sources](#credits--upstream-sources)
- [License](#license)

---

## What This Fixes

On Linux, the **Acer ALG AL15G-52** often boots with:

| Problem | Root Cause |
|---|---|
| `Fn + *` (backlight toggle), `Fn + -` / `Fn + +` (brightness) **do nothing** | BIOS drops Clevo hotkey `NEVT` events until the WMI hotkey driver activates (`clevo_wmi` + `tuxedo_keyboard`). |
| No way to change keyboard RGB color | Writing `/sys/class/leds/rgb:kbd_backlight/multi_intensity` requires root, and the color only takes effect when `brightness` is also written. |
| Random kernel panics or double-bind | `clevo_acpi` and `clevo_wmi` conflict if both are loaded simultaneously. |

**This project solves all three** with a one-command installer.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  alg-kbd-rgb  (Python GUI / CLI)                            │
│  ├── Reads / writes  /sys/class/leds/rgb:kbd_backlight/*    │
│  ├── UPower D-Bus fallback for brightness                   │
│  └── Saves & restores state via ~/.config/alg-kbd-rgb.json  │
├─────────────────────────────────────────────────────────────┤
│  udev rule  (99-alg-kbd-backlight.rules)                    │
│  └── chmod 0666 on multi_intensity & brightness at boot     │
├─────────────────────────────────────────────────────────────┤
│  Kernel modules  (DKMS: alg-tuxedo-kbd 4.25.1)             │
│  ├── tuxedo_compatibility_check                             │
│  ├── tuxedo_keyboard  ← activates Fn hotkeys                │
│  └── clevo_wmi        ← WMI interface for Clevo platform   │
├─────────────────────────────────────────────────────────────┤
│  modprobe.d / modules-load.d                                │
│  ├── Blacklists clevo_acpi to avoid conflicts               │
│  └── Auto-loads the three modules at boot                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Supported Distros

Tested and supported across major Linux distributions:

| Family | Distros | Package Manager |
|---|---|---|
| **Fedora** | Fedora, Nobara, RHEL | `dnf` |
| **Debian** | Ubuntu, Debian, Linux Mint, Pop!_OS | `apt-get` |
| **Arch** | Arch Linux, Manjaro, EndeavourOS, CachyOS | `pacman` |
| **SUSE** | openSUSE Tumbleweed / Leap | `zypper` |

> [!NOTE]
> **Secure Boot** must be disabled (or custom MOK signing configured) to load unsigned out-of-tree DKMS kernel modules.

---

## Quick Install

### Option A — From Git Clone

```bash
git clone https://github.com/Not-RK/acer-alg-kbd-rgb.git
cd acer-alg-kbd-rgb
sudo bash install.sh --install-deps
```

### Option B — From Pre-built Release (`.run` single-file installer)

Download the latest `.run` from the [Releases](https://github.com/Not-RK/acer-alg-kbd-rgb/releases) page:

```bash
chmod +x alg-kbd-rgb-4.25.1-linux.run
sudo ./alg-kbd-rgb-4.25.1-linux.run --install-deps
```

### Option C — From Release Tarball

```bash
tar xzf alg-kbd-rgb-4.25.1-linux.tar.gz
cd alg-kbd-rgb-pkg
sudo bash install.sh --install-deps
```

### Build Release Archives Locally

```bash
bash build-release.sh
```

Outputs `.run` and `.tar.gz` to the `dist/` directory.

### Installer Options

| Flag | Description |
|---|---|
| `--install-deps` | Auto-install missing build tools, kernel headers & GUI deps via your distro's package manager |
| `--no-deps` | Skip automatic dependency installation |
| `--skip-driver` | Only install the GUI, udev rules, and autostart (skip kernel module build) |
| `--rebuild-driver` | Force DKMS rebuild even if modules are already registered |

---

## Usage

### GUI

Open **Acer ALG Keyboard RGB** from your Application Menu, or run:

```bash
alg-kbd-rgb
```

Features:
- 10 quick-pick color presets with swatches
- Custom color picker dialog
- Brightness slider with Off / 50% / Max buttons
- Live sync — slider follows hardware `Fn + -` / `Fn + +` changes
- Auto-detects Qt (PySide6 → PyQt6 → PyQt5) or falls back to Tkinter

### CLI

```bash
# Set a custom RGB color
alg-kbd-rgb --set 0 160 255

# Set brightness (0–255)
alg-kbd-rgb --brightness 200

# Show current hardware state as JSON
alg-kbd-rgb --status

# Restore last saved color & brightness
alg-kbd-rgb --restore

# Force a specific GUI backend
alg-kbd-rgb --backend qt
alg-kbd-rgb --backend tk
```

### Hardware Hotkeys (after install)

| Hotkey | Action |
|---|---|
| `Fn + *` | Toggle keyboard backlight ON / OFF |
| `Fn + -` | Decrease brightness |
| `Fn + +` | Increase brightness |

---

## Uninstall

```bash
sudo bash uninstall.sh
```

Or if using the `.run` bundle:

```bash
sudo ./alg-kbd-rgb-4.25.1-linux.run --uninstall
```

> [!NOTE]
> Per-user config `~/.config/alg-kbd-rgb.json` is intentionally kept on uninstall.

---

## Project Structure

```
acer-alg-kbd-rgb/
├── alg_kbd_rgb.py          # Main Python GUI & CLI application (~620 lines)
├── alg-kbd-rgb.svg         # App icon (SVG, for desktop launcher)
├── install.sh              # Cross-distro installer (DKMS + GUI + udev + autostart)
├── uninstall.sh            # Clean uninstaller
├── build-release.sh        # Build .run & .tar.gz release archives
├── driver-src/             # Kernel module sources (from tuxedo-drivers v4.25.1)
│   ├── dkms.conf           # DKMS configuration
│   ├── Kbuild              # Top-level Kbuild
│   ├── Makefile            # Standalone build Makefile
│   └── src/
│       ├── clevo_wmi.c             # Clevo WMI interface driver
│       ├── clevo_interfaces.h      # Clevo WMI method definitions
│       ├── clevo_keyboard.h        # Clevo keyboard backlight/hotkey logic
│       ├── clevo_leds.h            # Clevo LED subsystem integration
│       ├── tuxedo_keyboard.c       # Main keyboard module entry point
│       ├── tuxedo_keyboard_common.h
│       ├── uniwill_interfaces.h    # Uniwill WMI method definitions
│       ├── uniwill_keyboard.h      # Uniwill keyboard support
│       ├── uniwill_leds.h          # Uniwill LED subsystem integration
│       └── tuxedo_compatibility_check/
│           ├── tuxedo_compatibility_check.c
│           └── tuxedo_compatibility_check.h
├── LICENSE                 # GPL-2.0-or-later (upstream copyright)
├── CREDITS.md              # Full upstream attribution & resources
└── .gitignore
```

---

## Credits & Upstream Sources

This project would not exist without the excellent work of the following open-source projects and communities. Full attribution in [CREDITS.md](CREDITS.md).

### Kernel Driver — TUXEDO Computers

The kernel modules in `driver-src/` are **derived from** the [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) project (release **v4.25.1**) by **TUXEDO Computers GmbH**.

| | |
|---|---|
| **Upstream Project** | [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) |
| **Upstream GitLab** | [gitlab.com/tuxedocomputers/development/packages/tuxedo-drivers](https://gitlab.com/tuxedocomputers/development/packages/tuxedo-drivers) |
| **Upstream Version** | v4.25.1 |
| **Copyright** | © 2018–2026 TUXEDO Computers GmbH <tux@tuxedocomputers.com> |
| **License** | [GPL-2.0-or-later](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) |

Only the **Clevo-specific subset** of the tuxedo-drivers tree is included here:
- `clevo_wmi.c` — WMI transport for Clevo BIOS
- `tuxedo_keyboard.c` — Platform keyboard module (Clevo + Uniwill dispatcher)
- `clevo_keyboard.h` / `clevo_leds.h` / `clevo_interfaces.h` — Clevo backlight & hotkey logic
- `uniwill_keyboard.h` / `uniwill_leds.h` / `uniwill_interfaces.h` — Uniwill support (compiled but not active on Clevo hardware)
- `tuxedo_compatibility_check/` — DMI-based platform allowlist
- `tuxedo_keyboard_common.h` — Shared definitions

### Related Projects & Resources

| Project | Description | Link |
|---|---|---|
| **tuxedo-drivers** | Full TUXEDO Computers kernel driver suite for keyboard, fan, and power management on Clevo/Uniwill laptops | [GitHub](https://github.com/tuxedocomputers/tuxedo-drivers) · [GitLab](https://gitlab.com/tuxedocomputers/development/packages/tuxedo-drivers) |
| **TUXEDO Control Center** | Official GUI for TUXEDO laptops (fan curves, power profiles, keyboard lighting) | [GitHub](https://github.com/tuxedocomputers/tuxedo-control-center) |
| **tuxedo-keyboard** (legacy) | Original standalone keyboard driver (predecessor to tuxedo-drivers) | [GitHub](https://github.com/tuxedocomputers/tuxedo-keyboard) |
| **Linux kernel `leds` subsystem** | Upstream kernel LED class used by `rgb:kbd_backlight` | [kernel.org docs](https://www.kernel.org/doc/html/latest/leds/index.html) |
| **Linux kernel `multicolor` LED** | Multi-color LED framework that provides `multi_intensity` sysfs | [kernel.org docs](https://www.kernel.org/doc/html/latest/leds/leds-class-multicolor.html) |
| **DKMS** | Dynamic Kernel Module Support — auto-rebuilds out-of-tree modules on kernel updates | [GitHub](https://github.com/dell/dkms) |
| **Clevo** | ODM/OEM that manufactures the barebone used in Acer ALG, TUXEDO, System76, and others | [clevo.com](https://www.clevo.com.tw/) |

### GUI Toolkit

The `alg-kbd-rgb` GUI auto-detects and uses one of:

| Toolkit | Project | License |
|---|---|---|
| **PySide6** (preferred) | [qt.io/qt-for-python](https://www.qt.io/qt-for-python) | LGPL-3.0 |
| **PyQt6** | [riverbankcomputing.com/software/pyqt](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0 |
| **PyQt5** | [riverbankcomputing.com/software/pyqt](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0 |
| **Tkinter** (fallback) | [docs.python.org/3/library/tkinter](https://docs.python.org/3/library/tkinter.html) | PSF |

---

## License

The kernel driver sources (`driver-src/`) are licensed under **GPL-2.0-or-later**, copyright © 2018–2026 TUXEDO Computers GmbH. See [LICENSE](LICENSE) for the full text.

The installer scripts, GUI application (`alg_kbd_rgb.py`), and all other files created by this project are also released under **GPL-2.0-or-later**.

```
SPDX-License-Identifier: GPL-2.0-or-later
```
