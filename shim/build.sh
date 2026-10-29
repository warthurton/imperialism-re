#!/bin/sh
# Build the display shim (a proxy msvfw32.dll for the 32-bit game).
# usage: ./build.sh [output.dll]      (default msvfw32.dll; install by copying it into the game folder, game closed)
# Needs the llvm-mingw toolchain (scoop package mingw-mstorsjo-llvm-ucrt); override with LLVM_MINGW=/path/to/bin.
BIN=${LLVM_MINGW:-$HOME/scoop/apps/mingw-mstorsjo-llvm-ucrt/current/bin}
cd "$(dirname "$0")" || exit 1
exec "$BIN/i686-w64-mingw32-clang" -O2 -Wall -shared -static -o "${1:-msvfw32.dll}" \
    shim.c msvfw32.def -luser32 -lgdi32 -ldwmapi
