#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail

PKG_NAME="alg-tuxedo-kbd"
PKG_VER="4.25.1"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo bash $0" >&2
  exit 1
fi

echo "[1/4] Removing GUI, icon, launcher & autostart..."
rm -f /usr/local/bin/alg-kbd-rgb \
      /usr/local/share/applications/alg-kbd-rgb.desktop \
      /usr/share/applications/alg-kbd-rgb.desktop \
      /usr/local/share/icons/hicolor/scalable/apps/alg-kbd-rgb.svg \
      /etc/xdg/autostart/alg-kbd-restore.desktop

if [[ -n "${SUDO_USER:-}" ]]; then
  UHOME="$(getent passwd "${SUDO_USER}" | cut -d: -f6 || true)"
  [[ -n "${UHOME}" ]] && rm -f "${UHOME}/.config/autostart/alg-kbd-restore.desktop"
fi

echo "[2/4] Removing udev, modules-load, and modprobe rules..."
rm -f /etc/udev/rules.d/99-alg-kbd-backlight.rules \
      /etc/modules-load.d/alg-tuxedo-kbd.conf \
      /etc/modprobe.d/alg-clevo.conf
udevadm control --reload-rules || true

echo "[3/4] Removing DKMS kernel module if registered..."
if command -v dkms >/dev/null 2>&1 && dkms status "${PKG_NAME}/${PKG_VER}" 2>/dev/null | grep -q "${PKG_NAME}"; then
  dkms remove "${PKG_NAME}/${PKG_VER}" --all || true
fi
rm -rf "/usr/src/${PKG_NAME}-${PKG_VER}"

echo "[4/4] Done! Note: Per-user config ~/.config/alg-kbd-rgb.json (if any) was kept."
