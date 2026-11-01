#!/bin/sh
# Compatibility entry point; active source now lives in Imperialism Compat.
# usage: ./build.sh [output.dll] (relative output paths are still relative to shim/)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
COMPAT=${IMPERIALISM_COMPAT:-"$HERE/../../imperialism-compat"}
[ -f "$COMPAT/build.py" ] || { echo "Clone https://github.com/warthurton/imperialism-compat beside imperialism-re, or set IMPERIALISM_COMPAT." >&2; exit 1; }
python -I "$COMPAT/build.py" --output "$HERE/build"
cd "$HERE"
cp build/msvfw32.dll "${1:-msvfw32.dll}"
