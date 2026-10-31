#!/bin/bash
set -u
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
exec /bin/bash "$ROOT/runtime/launch.sh" "$@"
