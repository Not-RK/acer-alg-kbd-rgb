#!/usr/bin/env bash
set -euo pipefail

PKG_NAME="alg-tuxedo-kbd"
PKG_VER="4.25.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_DEPS="auto"
SKIP_DRIVER=0
REBUILD_DRIVER=0

for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS="yes" ;;
    --no-deps)      INSTALL_DEPS="no" ;;
    --skip-driver)  SKIP_DRIVER=1 ;;
    --rebuild-driver) REBUILD_DRIVER=1 ;;
    -h|--help)
      cat <<'EOF'
Acer ALG AL15G-52 Keyboard RGB Cross-Distro Installer

Usage: sudo bash install.sh [OPTIONS]
  --install-deps     Automatically install missing build/GUI deps via distro package manager
  --no-deps          Do not invoke distro package manager
  --skip-driver      Skip kernel driver build/DKMS setup (install GUI + rules only)
  --rebuild-driver   Force rebuild/reinstall of DKMS/kernel modules
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo bash $0 $*" >&2
  exit 1
fi

KVER="$(uname -r)"
KBUILD_DIR="/lib/modules/${KVER}/build"

has_gui_toolkit() {
  python3 -c '
import importlib.util
for m in ("PySide6", "PyQt6", "PyQt5", "tkinter"):
    if importlib.util.find_spec(m) is not None:
        raise SystemExit(0)
raise SystemExit(1)
' >/dev/null 2>&1
}

detect_distro() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    echo "${ID:-unknown} ${ID_LIKE:-}"
  else
    echo "unknown"
  fi
}

install_distro_deps() {
  local need_build="$1"
  local need_gui="$2"
  local distro_info
  distro_info="$(detect_distro)"

  if command -v apt-get >/dev/null 2>&1; then
    local pkgs=()
    [[ "$need_build" == "1" ]] && pkgs+=(dkms build-essential "linux-headers-${KVER}")
    [[ "$need_gui" == "1" ]] && pkgs+=(python3 python3-tk python3-pyqt5)
    if [[ ${#pkgs[@]} -gt 0 ]]; then
      echo "Installing packages via apt-get: ${pkgs[*]}"
      apt-get update && apt-get install -y "${pkgs[@]}" || true
    fi
  elif command -v dnf >/dev/null 2>&1; then
    local pkgs=()
    [[ "$need_build" == "1" ]] && pkgs+=(dkms gcc make "kernel-devel-${KVER}" kernel-headers)
    [[ "$need_gui" == "1" ]] && pkgs+=(python3 python3-pyside6 python3-tkinter)
    if [[ ${#pkgs[@]} -gt 0 ]]; then
      echo "Installing packages via dnf: ${pkgs[*]}"
      dnf install -y "${pkgs[@]}" || true
    fi
  elif command -v pacman >/dev/null 2>&1; then
    local pkgs=()
    [[ "$need_build" == "1" ]] && pkgs+=(dkms base-devel linux-headers)
    [[ "$need_gui" == "1" ]] && pkgs+=(python pyside6 tk)
    if [[ ${#pkgs[@]} -gt 0 ]]; then
      echo "Installing packages via pacman: ${pkgs[*]}"
      pacman -Sy --noconfirm --needed "${pkgs[@]}" || true
    fi
  elif command -v zypper >/dev/null 2>&1; then
    local pkgs=()
    [[ "$need_build" == "1" ]] && pkgs+=(dkms gcc make kernel-default-devel)
    [[ "$need_gui" == "1" ]] && pkgs+=(python3 python3-qt5 python3-tk)
    if [[ ${#pkgs[@]} -gt 0 ]]; then
      echo "Installing packages via zypper: ${pkgs[*]}"
      zypper install -y "${pkgs[@]}" || true
    fi
  else
    echo "Distro package manager not recognized (${distro_info}). Please install make, gcc, kernel headers, dkms, and python3-tk / PySide6 manually if missing."
  fi
}

NEED_BUILD=0
NEED_GUI=0
if [[ "$SKIP_DRIVER" -eq 0 ]]; then
  if [[ ! -d "${KBUILD_DIR}" ]] || ! command -v make >/dev/null 2>&1 || ! command -v gcc >/dev/null 2>&1; then
    NEED_BUILD=1
  fi
fi
if ! has_gui_toolkit; then
  NEED_GUI=1
fi

if [[ "$NEED_BUILD" -eq 1 || "$NEED_GUI" -eq 1 ]]; then
  if [[ "$INSTALL_DEPS" == "yes" ]]; then
    install_distro_deps "$NEED_BUILD" "$NEED_GUI"
  elif [[ "$INSTALL_DEPS" == "auto" && -t 0 ]]; then
    echo "Missing components detected (kernel build tools/headers=${NEED_BUILD}, Python GUI toolkit=${NEED_GUI})."
    read -r -p "Install required packages using your distro package manager? [Y/n] " reply
    if [[ -z "$reply" || "$reply" =~ ^[Yy]$ ]]; then
      install_distro_deps "$NEED_BUILD" "$NEED_GUI"
    fi
  elif [[ "$INSTALL_DEPS" == "auto" ]]; then
    echo "Note: Non-interactive mode; run with --install-deps if kernel headers or GUI packages are missing."
  fi
fi

echo "[1/7] Installing GUI & CLI tool (/usr/local/bin/alg-kbd-rgb)..."
install -Dm0755 "${SCRIPT_DIR}/alg_kbd_rgb.py" /usr/local/bin/alg-kbd-rgb
install -Dm0644 "${SCRIPT_DIR}/alg-kbd-rgb.svg" /usr/local/share/icons/hicolor/scalable/apps/alg-kbd-rgb.svg

echo "[2/7] Installing desktop application launcher..."
mkdir -p /usr/local/share/applications
cat >/usr/local/share/applications/alg-kbd-rgb.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Acer ALG Keyboard RGB
Comment=Change keyboard RGB backlight color and brightness
Exec=/usr/local/bin/alg-kbd-rgb
Icon=alg-kbd-rgb
Terminal=false
Categories=Settings;HardwareSettings;Utility;
Keywords=keyboard;rgb;backlight;color;acer;alg;
EOF
chmod 0644 /usr/local/share/applications/alg-kbd-rgb.desktop
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/local/share/applications >/dev/null 2>&1 || true
fi

echo "[3/7] Setting udev permissions for passwordless RGB & brightness control..."
mkdir -p /etc/udev/rules.d
cat >/etc/udev/rules.d/99-alg-kbd-backlight.rules <<'EOF'
ACTION=="add", SUBSYSTEM=="leds", KERNEL=="rgb:kbd_backlight", RUN+="/bin/chmod 0666 /sys/class/leds/rgb:kbd_backlight/multi_intensity /sys/class/leds/rgb:kbd_backlight/brightness"
EOF
chmod 0644 /etc/udev/rules.d/99-alg-kbd-backlight.rules

echo "[4/7] Configuring kernel module auto-load & clevo_acpi conflict blacklist..."
mkdir -p /etc/modules-load.d /etc/modprobe.d
cat >/etc/modules-load.d/alg-tuxedo-kbd.conf <<'EOF'
tuxedo_compatibility_check
tuxedo_keyboard
clevo_wmi
EOF
chmod 0644 /etc/modules-load.d/alg-tuxedo-kbd.conf

cat >/etc/modprobe.d/alg-clevo.conf <<'EOF'
blacklist clevo_acpi
EOF
chmod 0644 /etc/modprobe.d/alg-clevo.conf

echo "[5/7] Setting desktop-agnostic login autostart to restore saved RGB color..."
mkdir -p /etc/xdg/autostart
cat >/etc/xdg/autostart/alg-kbd-restore.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Acer ALG Keyboard RGB Restore
Comment=Restore saved keyboard RGB color on login
Exec=/usr/local/bin/alg-kbd-rgb --restore
Terminal=false
X-GNOME-Autostart-enabled=true
X-KDE-autostart-phase=2
EOF
chmod 0644 /etc/xdg/autostart/alg-kbd-restore.desktop

echo "[6/7] Installing kernel driver (${PKG_NAME} ${PKG_VER})..."
if [[ "$SKIP_DRIVER" -eq 1 ]]; then
  echo "  -> Skipped (--skip-driver)"
else
  ALREADY_READY=0
  if [[ "$REBUILD_DRIVER" -eq 0 ]] && modinfo clevo_wmi >/dev/null 2>&1 && modinfo tuxedo_keyboard >/dev/null 2>&1; then
    ALREADY_READY=1
  fi

  if [[ "$ALREADY_READY" -eq 1 ]] && ! command -v dkms >/dev/null 2>&1; then
    echo "  -> Existing clevo_wmi & tuxedo_keyboard found for kernel ${KVER}; keeping them."
  elif command -v dkms >/dev/null 2>&1 && [[ -d "${KBUILD_DIR}" ]]; then
    if dkms status "${PKG_NAME}/${PKG_VER}" 2>/dev/null | grep -q "${PKG_NAME}"; then
      if [[ "$REBUILD_DRIVER" -eq 1 ]]; then
        dkms remove "${PKG_NAME}/${PKG_VER}" --all || true
      else
        echo "  -> DKMS module ${PKG_NAME}/${PKG_VER} already registered; ensuring installed for ${KVER}..."
      fi
    fi
    if ! dkms status "${PKG_NAME}/${PKG_VER}" 2>/dev/null | grep -q "${PKG_NAME}"; then
      rm -rf "/usr/src/${PKG_NAME}-${PKG_VER}"
      mkdir -p "/usr/src/${PKG_NAME}-${PKG_VER}"
      cp -a "${SCRIPT_DIR}/driver-src/." "/usr/src/${PKG_NAME}-${PKG_VER}/"
      dkms add -m "${PKG_NAME}" -v "${PKG_VER}"
    fi
    dkms build -m "${PKG_NAME}" -v "${PKG_VER}" -k "${KVER}"
    dkms install -m "${PKG_NAME}" -v "${PKG_VER}" -k "${KVER}"
  elif [[ -d "${KBUILD_DIR}" ]] && command -v make >/dev/null 2>&1; then
    echo "  -> DKMS not installed; building directly for kernel ${KVER}..."
    TMP_DRV="$(mktemp -d)"
    cp -a "${SCRIPT_DIR}/driver-src/." "${TMP_DRV}/"
    make -C "${TMP_DRV}" KVER="${KVER}"
    make -C "${TMP_DRV}" KVER="${KVER}" install
    rm -rf "${TMP_DRV}"
  else
    echo "Warning: Kernel headers (${KBUILD_DIR}) or make missing; could not compile kernel driver." >&2
    echo "Re-run after installing kernel headers & build tools: sudo bash $0 --install-deps" >&2
  fi
fi

echo "[7/7] Loading drivers & applying permissions now..."
if lsmod | grep -q '^clevo_acpi '; then
  rmmod clevo_acpi || true
fi
modprobe tuxedo_compatibility_check tuxedo_keyboard clevo_wmi 2>/dev/null || {
  modprobe tuxedo_compatibility_check || true
  modprobe tuxedo_keyboard || true
  modprobe clevo_wmi || true
}
udevadm control --reload-rules || true
udevadm trigger --subsystem-match=leds || true
if [[ -d /sys/class/leds/rgb:kbd_backlight ]]; then
  chmod 0666 /sys/class/leds/rgb:kbd_backlight/multi_intensity /sys/class/leds/rgb:kbd_backlight/brightness || true
fi

echo ""
echo "Installation complete!"
echo "Open 'Acer ALG Keyboard RGB' from your Application Menu, or run: alg-kbd-rgb"
