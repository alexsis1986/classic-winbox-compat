#!/bin/bash
# Per-user install only; no root, no network, no Wine installation.
set -eu
set -o pipefail
umask 077
case "$(uname -s)/$(uname -m)" in Linux/x86_64|Linux/amd64) ;; *) echo 'This package targets Linux x86-64 only.' >&2; exit 1 ;; esac
[ "$(id -u)" != 0 ] || { echo 'Use your normal desktop account; do not use sudo.' >&2; exit 1; }
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
case "$DATA" in /*) ;; *) echo 'XDG_DATA_HOME must be absolute.' >&2; exit 1 ;; esac
case "$DATA" in *$'\n'*|*$'\r'*|*$'\t'*) echo 'Control characters in the installation path are not supported.' >&2; exit 1 ;; esac
[ ! -L "$DATA/classic-winbox343" ] || { echo 'Refusing a symlinked application directory.' >&2; exit 1; }
DEST="$DATA/classic-winbox343/app-0.1.0-preview"
DESKTOP="$DATA/applications/classic-winbox343.desktop"
[ ! -e "$DEST" ] && [ ! -L "$DEST" ] || { echo "Already exists: $DEST. No files were changed. Run its WinBox.sh or use a different test location." >&2; exit 1; }
[ ! -e "$DESKTOP" ] && [ ! -L "$DESKTOP" ] || { echo "Shortcut already exists: $DESKTOP. No files were changed." >&2; exit 1; }
# Do not install an incomplete/corrupted payload. A runtime is not required here.
EXPECTED='ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
[ "$(sha256sum "$ROOT/runtime/payload/winbox64.exe" | awk '{print $1}')" = "$EXPECTED" ] || { echo 'Payload hash mismatch.' >&2; exit 1; }
mkdir -p "$DEST" "$DATA/applications"
cp -R "$ROOT/runtime" "$DEST/"
cp "$ROOT/WinBox.sh" "$ROOT/README_RU.md" "$DEST/"
for DOC in README_EN.md NOTICE.txt WRAPPER_LICENSE.txt SOURCES.md; do
    if [ -f "$ROOT/$DOC" ]; then cp "$ROOT/$DOC" "$DEST/"; fi
done
chmod 700 "$DEST/WinBox.sh" "$DEST/runtime/launch.sh"
# Exec is NOT a shell command. Escape the .desktop and Exec quoting layers.
EXEC=$(printf '%s' "$DEST/WinBox.sh" | sed -e 's/\\/\\\\\\\\/g' -e 's/"/\\\\"/g' -e 's/`/\\\\`/g' -e 's/\$/\\\\$/g' -e 's/%/%%/g')
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Classic WinBox 3.43 (Preview)
Comment=Unofficial WinBox 3.43 compatibility launcher through Wine
Exec=/bin/bash "$EXEC" --gui
Icon=network-workgroup
Terminal=false
Categories=Network;System;
StartupNotify=false
EOF
chmod 600 "$DESKTOP"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DATA/applications" >/dev/null 2>&1 || true
fi
printf 'Installed: %s\nShortcut: %s\n' "$DEST" "$DESKTOP"
printf 'Next: install Wine if needed, then run:\n  bash "%s/WinBox.sh" --doctor\n' "$DEST"
