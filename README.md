# Acer ALG AL15G-52 Keyboard RGB & Backlight Fix for Linux

Universal cross-distro Linux driver setup, DKMS package, and GUI/CLI tool to fix keyboard backlight hotkeys and control RGB colors on the **Acer ALG AL15G-52** (Clevo WMI platform).

## What This Fixes
On Linux, the Acer ALG AL15G-52 often boots with keyboard backlight hotkeys non-functional (`Fn + *` toggle, `Fn + -` / `Fn + +` brightness) and no easy way to change RGB colors because:
1. BIOS drops Clevo hotkey `NEVT` events until the WMI hotkey driver activates (`clevo_wmi` + `tuxedo_keyboard`).
2. `clevo_acpi` can conflict with `clevo_wmi` if both are loaded.
3. Writing `/sys/class/leds/rgb:kbd_backlight/multi_intensity` requires root permissions by default and only takes effect when `brightness` is also written.

This repository packages:
- **Minimal DKMS kernel module (`alg-tuxedo-kbd` 4.25.1):** `tuxedo_compatibility_check`, `tuxedo_keyboard`, and `clevo_wmi` (kernel >= 7.2+ compatible), auto-rebuilt across kernel updates via DKMS.
- **Cross-distro `alg-kbd-rgb` GUI & CLI:** Uses native Qt (`PySide6` / `PyQt6` / `PyQt5`) on KDE/Qt desktops and automatically falls back to built-in `Tkinter` on GNOME, XFCE, Cinnamon, etc.
- **System integration:** `clevo_acpi` blacklist, `modules-load.d` boot loading, `udev` rule for passwordless RGB & brightness updates, desktop entry + SVG icon, and desktop-agnostic XDG autostart to restore your saved color on login.

## Supported Distros
Tested / supported across major Linux distributions:
- **Fedora / Nobara / RHEL** (`dnf`)
- **Ubuntu / Debian / Linux Mint / Pop!_OS** (`apt-get`)
- **Arch Linux / Manjaro / EndeavourOS / CachyOS** (`pacman`)
- **openSUSE** (`zypper`)

## Quick Install

### From Git Clone
```bash
git clone https://github.com/<YOUR_USERNAME>/acer-alg-kbd-rgb.git
cd acer-alg-kbd-rgb
sudo bash install.sh --install-deps
```

### From Release Single-File Installer (`.run`)
```bash
chmod +x alg-kbd-rgb-4.25.1-linux.run
sudo ./alg-kbd-rgb-4.25.1-linux.run --install-deps
```

### Build Release Archives Locally (`.run` & `.tar.gz`)
```bash
bash build-release.sh
```
Outputs are written to `dist/`.

> **Note:** Secure Boot must be disabled (or custom MOK signing configured) to load unsigned out-of-tree DKMS kernel modules.

## Usage
- **App Menu:** Open **Acer ALG Keyboard RGB**
- **GUI:** `alg-kbd-rgb`
- **CLI:**
  - `alg-kbd-rgb --set 0 160 255` — Set custom RGB color (`0–255`)
  - `alg-kbd-rgb --brightness 200` — Set brightness (`0–255`)
  - `alg-kbd-rgb --status` — Show current hardware & saved state as JSON
  - `alg-kbd-rgb --restore` — Re-apply last saved RGB & brightness

## Hardware Hotkeys
Once installed:
- `Fn + *` — Toggle keyboard backlight ON / OFF
- `Fn + -` / `Fn + +` — Decrease / increase keyboard brightness

## Uninstall
```bash
sudo bash uninstall.sh
```
Or if using the `.run` bundle:
```bash
sudo ./alg-kbd-rgb-4.25.1-linux.run --uninstall
```

## Credits & License
- Kernel driver sources (`driver-src/`) are derived from [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) (v4.25.1) under **GPL-2.0-or-later** (see `LICENSE`).
