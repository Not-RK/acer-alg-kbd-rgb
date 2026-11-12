#!/usr/bin/env bash
set -euo pipefail

PKG_NAME="alg-kbd-rgb"
VERSION="4.25.1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "${STAGE_DIR}"' EXIT

mkdir -p "${DIST_DIR}"
mkdir -p "${STAGE_DIR}/alg-kbd-rgb-pkg"

cp -a \
  "${ROOT_DIR}/README.md" \
  "${ROOT_DIR}/LICENSE" \
  "${ROOT_DIR}/alg-kbd-rgb.svg" \
  "${ROOT_DIR}/alg_kbd_rgb.py" \
  "${ROOT_DIR}/install.sh" \
  "${ROOT_DIR}/uninstall.sh" \
  "${ROOT_DIR}/driver-src" \
  "${STAGE_DIR}/alg-kbd-rgb-pkg/"

chmod +x \
  "${STAGE_DIR}/alg-kbd-rgb-pkg/alg_kbd_rgb.py" \
  "${STAGE_DIR}/alg-kbd-rgb-pkg/install.sh" \
  "${STAGE_DIR}/alg-kbd-rgb-pkg/uninstall.sh"

TARBALL="${DIST_DIR}/${PKG_NAME}-${VERSION}-linux.tar.gz"
RUNFILE="${DIST_DIR}/${PKG_NAME}-${VERSION}-linux.run"

tar -czf "${TARBALL}" -C "${STAGE_DIR}" "alg-kbd-rgb-pkg"

cat > "${RUNFILE}" <<'RUN_EOF'
#!/usr/bin/env bash
set -euo pipefail

ACTION="install"
PASS_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --extract-only) ACTION="extract" ;;
    --uninstall)    ACTION="uninstall" ;;
    *)              PASS_ARGS+=("$arg") ;;
  esac
done

ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__$/ {print NR + 1; exit 0}' "$0")
if [[ "$ACTION" == "extract" ]]; then
  tail -n "+${ARCHIVE_LINE}" "$0" | tar -xz
  echo "Extracted to ./alg-kbd-rgb-pkg"
  exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT
tail -n "+${ARCHIVE_LINE}" "$0" | tar -xz -C "${TMP_DIR}"

if [[ "$ACTION" == "uninstall" ]]; then
  bash "${TMP_DIR}/alg-kbd-rgb-pkg/uninstall.sh" ${PASS_ARGS[@]+"${PASS_ARGS[@]}"}
else
  bash "${TMP_DIR}/alg-kbd-rgb-pkg/install.sh" ${PASS_ARGS[@]+"${PASS_ARGS[@]}"}
fi
exit $?
__ARCHIVE_BELOW__
RUN_EOF

cat "${TARBALL}" >> "${RUNFILE}"
chmod +x "${RUNFILE}"

echo "Built:"
ls -lh "${TARBALL}" "${RUNFILE}"
