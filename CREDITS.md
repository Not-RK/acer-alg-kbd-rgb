# Credits & Upstream Attribution

This project builds on the work of several open-source projects. This file provides full attribution as required by their respective licenses.

---

## Kernel Driver Sources — TUXEDO Computers GmbH

The kernel modules in [`driver-src/`](driver-src/) are **derived from** the **tuxedo-drivers** project by **TUXEDO Computers GmbH**.

- **Upstream Repository (GitHub):** https://github.com/tuxedocomputers/tuxedo-drivers
- **Upstream Repository (GitLab):** https://gitlab.com/tuxedocomputers/development/packages/tuxedo-drivers
- **Upstream Version Used:** v4.25.1
- **Copyright:** © 2018–2026 TUXEDO Computers GmbH <tux@tuxedocomputers.com>
- **License:** [GPL-2.0-or-later](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **SPDX Identifier:** `GPL-2.0+`

### What Was Taken

Only the **Clevo WMI keyboard/LED subset** of the full tuxedo-drivers tree was extracted for use in this project. The following files are directly derived from tuxedo-drivers v4.25.1:

| File | Upstream Path | Description |
|---|---|---|
| `driver-src/src/clevo_wmi.c` | `src/clevo_wmi.c` | WMI transport driver for Clevo BIOS |
| `driver-src/src/clevo_interfaces.h` | `src/clevo_interfaces.h` | Clevo WMI method IDs and interface definitions |
| `driver-src/src/clevo_keyboard.h` | `src/clevo_keyboard.h` | Clevo keyboard backlight & Fn hotkey handler |
| `driver-src/src/clevo_leds.h` | `src/clevo_leds.h` | Clevo multicolor LED class integration |
| `driver-src/src/tuxedo_keyboard.c` | `src/tuxedo_keyboard.c` | Main module entry point (Clevo + Uniwill dispatcher) |
| `driver-src/src/tuxedo_keyboard_common.h` | `src/tuxedo_keyboard_common.h` | Shared constants and structures |
| `driver-src/src/uniwill_interfaces.h` | `src/uniwill_interfaces.h` | Uniwill WMI method definitions |
| `driver-src/src/uniwill_keyboard.h` | `src/uniwill_keyboard.h` | Uniwill keyboard support (compiled, not active on Clevo) |
| `driver-src/src/uniwill_leds.h` | `src/uniwill_leds.h` | Uniwill LED subsystem integration |
| `driver-src/src/tuxedo_compatibility_check/` | `src/tuxedo_compatibility_check/` | DMI-based platform compatibility check module |
| `driver-src/dkms.conf` | — | Custom DKMS config for this subset (written by this project) |
| `driver-src/Kbuild` | — | Custom top-level Kbuild (written by this project) |
| `driver-src/Makefile` | — | Standalone build Makefile (written by this project) |

### What Was Modified

- **`dkms.conf`** was written from scratch to build only the three modules needed: `tuxedo_compatibility_check`, `tuxedo_keyboard`, and `clevo_wmi`.
- **`Kbuild`** and **`Makefile`** were simplified for standalone/DKMS build of the Clevo subset only.
- No modifications were made to the C source files or headers themselves.

---

## Related Upstream Projects

### TUXEDO Control Center
- **URL:** https://github.com/tuxedocomputers/tuxedo-control-center
- **Description:** Official TUXEDO GUI application for fan control, power profiles, and keyboard lighting on TUXEDO laptops.
- **License:** GPL-3.0

### tuxedo-keyboard (Legacy)
- **URL:** https://github.com/tuxedocomputers/tuxedo-keyboard
- **Description:** The original standalone keyboard backlight driver, now superseded by tuxedo-drivers.
- **License:** GPL-2.0+

---

## Linux Kernel Subsystems Used

| Subsystem | Documentation |
|---|---|
| LED class (`/sys/class/leds/`) | https://www.kernel.org/doc/html/latest/leds/index.html |
| Multicolor LED framework (`multi_intensity`) | https://www.kernel.org/doc/html/latest/leds/leds-class-multicolor.html |
| WMI bus (`wmi_driver`) | https://www.kernel.org/doc/html/latest/wmi/index.html |
| ACPI | https://www.kernel.org/doc/html/latest/driver-api/acpi/index.html |

---

## Build & Packaging Tools

| Tool | URL | Purpose |
|---|---|---|
| **DKMS** | https://github.com/dell/dkms | Dynamic Kernel Module Support — auto-rebuilds modules on kernel updates |
| **GNU Make** | https://www.gnu.org/software/make/ | Build system for kernel modules |
| **GCC** | https://gcc.gnu.org/ | Compiler for kernel modules |

---

## Python GUI Toolkits

The `alg-kbd-rgb` GUI application is written in Python 3 and auto-detects one of the following toolkits at runtime:

| Toolkit | URL | License | Notes |
|---|---|---|---|
| **PySide6** | https://www.qt.io/qt-for-python | LGPL-3.0 | Preferred on KDE/Qt desktops |
| **PyQt6** | https://www.riverbankcomputing.com/software/pyqt/ | GPL-3.0 | Alternative Qt binding |
| **PyQt5** | https://www.riverbankcomputing.com/software/pyqt/ | GPL-3.0 | Legacy Qt5 binding |
| **Tkinter** | https://docs.python.org/3/library/tkinter.html | PSF License | Built-in fallback (GNOME, XFCE, etc.) |

---

## Hardware

- **Clevo** — ODM that manufactures the barebone chassis used in Acer ALG, TUXEDO, System76, Metabox, and many other brands.
  - Website: https://www.clevo.com.tw/

- **Acer ALG AL15G-52** — The specific laptop model this project targets. Uses Clevo WMI internally for keyboard backlight control.

---

## Acknowledgements

Special thanks to:
- The **TUXEDO Computers** team for open-sourcing their kernel drivers and making them available under GPL-2.0+.
- The **Linux kernel LED subsystem maintainers** for the multicolor LED framework that makes RGB keyboard control possible through sysfs.
- The **DKMS maintainers** (originally Dell, now community-maintained) for making out-of-tree module management seamless across kernel updates.
- The **Clevo reverse-engineering community** for documenting the WMI interface used by Clevo-based laptops.
