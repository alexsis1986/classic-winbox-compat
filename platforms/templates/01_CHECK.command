#!/bin/bash
set -u
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
/bin/bash "$ROOT/Classic WinBox 3.43.app/Contents/Resources/launch.sh" --doctor
RESULT=$?
printf '\nCheck exit code: %s\n' "$RESULT"
if [ -t 0 ]; then printf 'Press Enter to close...'; IFS= read -r _ || true; fi
exit "$RESULT"
