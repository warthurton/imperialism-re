#!/bin/sh
# Compatibility entry point; canonical build and both codec variants live in Imperialism Compat.
# usage: ./build.sh <path to the game's libvorbisfile-3.dll> [output.dll]
# Output goes next to this script (build/), never into the game folder; copy it over winmm.dll yourself.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
COMPAT=${IMPERIALISM_COMPAT:-"$HERE/../../imperialism-compat"}
[ -f "$COMPAT/tools/build_music.py" ] || { echo "Clone https://github.com/warthurton/imperialism-compat beside imperialism-re, or set IMPERIALISM_COMPAT." >&2; exit 1; }
VF=${1:?path to libvorbisfile-3.dll}
OUT=${2:-$HERE/build/winmm.dll}
python -I "$COMPAT/tools/fetch_deps.py"
python -I "$COMPAT/tools/build_music.py" --game-codec "$VF"
mkdir -p "$(dirname "$OUT")"
cp "$COMPAT/build/music/gog-codecs/winmm.dll" "$OUT"
echo "built $OUT"
