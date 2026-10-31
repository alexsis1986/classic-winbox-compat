#!/bin/bash
set -eu
set -o pipefail
umask 077
[ "$(uname -s)" = Darwin ] || { echo 'Run this installer on macOS.' >&2; exit 1; }
[ "$(id -u)" != 0 ] || { echo 'Do not use sudo.' >&2; exit 1; }
[ -n "${HOME:-}" ] || { echo "HOME is missing." >&2; exit 1; }
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
SOURCE="$ROOT/Classic WinBox 3.43.app"
DEST="$HOME/Applications/Classic WinBox 3.43.app"
[ ! -e "$DEST" ] && [ ! -L "$DEST" ] || { echo "Already exists: $DEST. It was NOT replaced." >&2; exit 1; }
EXPECTED='ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
[ "$(shasum -a 256 "$SOURCE/Contents/Resources/payload/winbox64.exe" | awk '{print $1}')" = "$EXPECTED" ] || { echo 'Payload hash mismatch.' >&2; exit 1; }
mkdir -p "$HOME/Applications"
/usr/bin/ditto "$SOURCE" "$DEST"
chmod u+x "$DEST/Contents/MacOS/ClassicWinBox" "$DEST/Contents/Resources/launch.sh"
printf 'Installed: %s\nNo system protection settings were changed.\n' "$DEST"
printf 'Wine is required separately. See README_RU.md, then open the app.\n'
