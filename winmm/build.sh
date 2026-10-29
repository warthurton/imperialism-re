#!/bin/sh
# Rebuild the music DLL that replaces GOG's CD-audio winmm.dll: the maintained open-source ogg-winmm
# (GPLv2) at a pinned commit, built from source and linked against the game's OWN libvorbisfile-3.dll
# (only the headers come from the clone; no prebuilt third-party binaries are linked).
# usage: ./build.sh <path to the game's libvorbisfile-3.dll> [output.dll]
# Output goes next to this script (build/), never into the game folder; copy it over winmm.dll yourself.
set -e
PIN=11c13ecf727fc0b00b46e04acbf503a60e7df1db            # ayuanx/ogg-winmm, 2025-06-20
BIN=${LLVM_MINGW:-$HOME/scoop/apps/mingw-mstorsjo-llvm-ucrt/current/bin}
HERE=$(cd "$(dirname "$0")" && pwd)
VF=${1:?path to libvorbisfile-3.dll}
OUT=${2:-$HERE/build/winmm.dll}
SRC=$HERE/build/ogg-winmm
mkdir -p "$HERE/build"
[ -d "$SRC" ] || git clone https://github.com/ayuanx/ogg-winmm.git "$SRC"
git -C "$SRC" checkout -q "$PIN"

# import library for the game's libvorbisfile DLL
"$BIN/llvm-readobj" --coff-exports "$VF" | awk '/Name:/ {print $2}' > "$HERE/build/vf_exports.txt"
{ echo "LIBRARY libvorbisfile-3.dll"; echo "EXPORTS"; cat "$HERE/build/vf_exports.txt"; } > "$HERE/build/vf.def"
"$BIN/llvm-dlltool" -m i386 -d "$HERE/build/vf.def" -l "$HERE/build/libvorbisfile_imp.a"

"$BIN/i686-w64-mingw32-clang" -std=gnu99 -O2 -Wall -Wno-unused-function -Wno-unused-variable -Wno-format \
    -shared -static -Wl,--enable-stdcall-fixup -o "$OUT" \
    "$SRC/ogg-winmm.c" "$SRC/player.c" "$SRC/stubs.c" "$SRC/ogg-winmm.def" \
    -I"$SRC/libs/include" -L"$HERE/build" -l:libvorbisfile_imp.a -lwinmm
echo "built $OUT"
