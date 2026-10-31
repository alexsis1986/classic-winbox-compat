#!/bin/bash
# Classic WinBox 3.43: private Wine launcher, no router credentials or arguments.
# Compatible syntax target: bash 3.2+. No eval, sudo, Gatekeeper or firewall edits.
set -u
set -o pipefail
umask 077
EXPECTED_SHA256='ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
EXE="$ROOT/payload/winbox64.exe"
MODE=run
GUI=0
OS=$(uname -s)
CPU=$(uname -m)
case "${1:-}" in
    --doctor) MODE=doctor; shift ;;
    --gui) GUI=1; shift ;;
    -psn_*) GUI=1; shift ;;
esac
fail() {
    printf 'STOP: %s\n' "$*" >&2
    if [ "$GUI" = 1 ]; then
        if [ "$OS" = Darwin ] && [ -x /usr/bin/osascript ]; then
            /usr/bin/osascript - "$*" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run argv
    display alert "Classic WinBox 3.43" message (item 1 of argv) as warning
end run
APPLESCRIPT
        elif command -v zenity >/dev/null 2>&1; then
            zenity --error --title='Classic WinBox 3.43' --text="$*" >/dev/null 2>&1 || true
        fi
    fi
    exit 1
}
[ "$#" -eq 0 ] || fail 'Router addresses, usernames and passwords are not accepted as command-line arguments. Enter them in WinBox.'
[ "$(id -u)" != 0 ] || fail 'Do not run WinBox/Wine as root. Use your normal desktop account.'
[ -n "${HOME:-}" ] || fail 'HOME is not set.'
case "$HOME" in /*) ;; *) fail 'HOME must be an absolute path.' ;; esac
case "$OS/$CPU" in
    Linux/x86_64|Linux/amd64) ;;
    Darwin/x86_64|Darwin/arm64) ;;
    *) fail "Unsupported platform: $OS/$CPU. This is a Windows x64 EXE; Linux ARM is not supported by this kit." ;;
esac
[ -f "$EXE" ] && [ ! -L "$EXE" ] || fail 'The bundled WinBox payload is missing or is a symlink.'
if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL=$(sha256sum "$EXE" | awk '{print $1}') || fail 'SHA-256 could not be calculated.'
elif command -v shasum >/dev/null 2>&1; then
    ACTUAL=$(shasum -a 256 "$EXE" | awk '{print $1}') || fail 'SHA-256 could not be calculated.'
else
    fail 'Install a SHA-256 utility (sha256sum or shasum).'
fi
[ "$ACTUAL" = "$EXPECTED_SHA256" ] || fail 'WinBox SHA-256 mismatch. Nothing was launched. Restore this package; do not turn off verification.'
if [ "$OS" = Darwin ]; then
    DATA="$HOME/Library/Application Support/ClassicWinBox343"
    CONFIG="$DATA/wine-path.txt"
    if [ "$CPU" = arm64 ]; then
        /usr/bin/arch -x86_64 /usr/bin/true >/dev/null 2>&1 || fail 'The Intel Wine route requires Rosetta 2. Use the normal macOS installation prompt; this launcher does not install Rosetta.'
    fi
else
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}/classic-winbox343"
    CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/classic-winbox343/wine-path.txt"
fi
case "$DATA" in /*) ;; *) fail 'The data directory must be absolute.' ;; esac
WINE=''
if [ -n "${CWC_WINE_BIN:-}" ]; then
    WINE=$CWC_WINE_BIN
elif [ -f "$CONFIG" ]; then
    IFS= read -r WINE < "$CONFIG" || true
    WINE=${WINE%$'\r'}
    [ -n "$WINE" ] || fail 'The Wine path file is empty. Supply one absolute executable path.'
fi
if [ -n "$WINE" ]; then
    case "$WINE" in /*) ;; *) fail 'The configured Wine path must be absolute (no arguments, no quotes).' ;; esac
    [ -f "$WINE" ] && [ -x "$WINE" ] || fail 'The configured Wine executable does not exist or is not executable.'
else
    for NAME in wine wine64; do
        CANDIDATE=$(command -v "$NAME" 2>/dev/null || true)
        if [ -n "$CANDIDATE" ] && [ -f "$CANDIDATE" ] && [ -x "$CANDIDATE" ]; then WINE=$CANDIDATE; break; fi
    done
    if [ -z "$WINE" ] && [ "$OS" = Darwin ]; then
        for BASE in /Applications "$HOME/Applications"; do
            for APP in 'Wine Stable.app' 'Wine Devel.app' 'Wine Staging.app'; do
                for BIN in wine wine64; do
                    CANDIDATE="$BASE/$APP/Contents/Resources/wine/bin/$BIN"
                    if [ -x "$CANDIDATE" ] && [ -f "$CANDIDATE" ]; then WINE=$CANDIDATE; break 3; fi
                done
            done
        done
        if [ -z "$WINE" ]; then
            for CANDIDATE in /opt/homebrew/bin/wine /usr/local/bin/wine /opt/local/bin/wine; do
                if [ -x "$CANDIDATE" ]; then WINE=$CANDIDATE; break; fi
            done
        fi
    fi
fi
[ -n "$WINE" ] || fail 'Wine was not found. Install a trusted Windows-x64-capable Wine runtime first; see README_RU.md. Wine is not included.'
VERSION=$("$WINE" --version 2>&1) || fail 'Wine itself cannot start. Check its dependencies, architecture and macOS approval. No WinBox was launched.'
# Prevent an inherited wine32 setting from overriding the private 64-bit prefix.
PREFIX="$DATA/wineprefix"
if [ "$MODE" = doctor ]; then
    printf 'Platform: %s / %s\nEXE SHA-256: PASS\nWine: %s\nRuntime: %s\nPrefix: %s\n' "$OS" "$CPU" "$WINE" "$VERSION" "$PREFIX"
    if [ "$OS" = Linux ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
        fail 'No graphical session was found. Run in your Linux desktop session (X11/XWayland or compatible Wine Wayland driver).'
    fi
    [ "$(id -u)" != 0 ] || fail 'Do not run WinBox/Wine as root.'
    printf 'Environment check: PASS. WinBox was NOT started; router connectivity is NOT tested.\n'
    exit 0
fi
[ "$(id -u)" != 0 ] || fail 'Do not run WinBox/Wine as root. Use your normal desktop account.'
if [ "$OS" = Linux ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    fail 'No graphical session was found. Run this launcher from the desktop, not a headless SSH shell.'
fi
[ ! -L "$DATA" ] && [ ! -L "$PREFIX" ] || fail 'Refusing a symlinked data directory or Wine prefix.'
mkdir -p "$DATA" "$DATA/logs" || fail 'Cannot create private application data.'
[ -O "$DATA" ] && [ -O "$DATA/logs" ] || fail 'Application data must be owned by the current account.'
[ ! -L "$DATA/logs" ] || fail 'Refusing a symlinked log directory.'
chmod 700 "$DATA" "$DATA/logs" || fail 'Cannot protect the data directory.'
if [ -f "$PREFIX/system.reg" ] && grep -q '^#arch=win32' "$PREFIX/system.reg"; then
    fail 'This application-specific Wine prefix is 32-bit. It was left unchanged; a 64-bit-capable prefix is required.'
fi
# Sessions stay in this private prefix. This is isolation from other Wine apps,
# NOT an operating-system security sandbox.
export WINEPREFIX="$PREFIX"
export WINEARCH=win64
export WINEDEBUG="${WINEDEBUG:--all}"
LOG="$DATA/logs/last-launch.log"
[ ! -L "$LOG" ] || fail 'Refusing a symlinked log file.'
# Keep only the latest launch log. It can contain personal paths or Wine output.
printf 'Classic WinBox 3.43 / platform preview 0.1.0\nEXE hash: verified\nWine: %s\n' "$VERSION" > "$LOG" || fail 'Cannot create the launch log.'
cd "$DATA" || fail 'Cannot enter the data directory.'
"$WINE" "$EXE" >> "$LOG" 2>&1
RESULT=$?
if [ "$RESULT" -ne 0 ]; then fail "Wine/WinBox exited with code $RESULT. Private log: $LOG"; fi
exit 0
