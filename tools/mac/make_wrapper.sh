#!/bin/sh
# Build a private Wine-wrapped copy of Imperialism on macOS.  UNTESTED (written without a Mac); see docs/mac_ipad.md.
# Usage: sh tools/mac/make_wrapper.sh /path/to/your/GOG/Imperialism   [output folder, default ~/ImperialismMac]
# Never commit or share the output: it contains the game's copyrighted files.
set -e
src="$1"
out="${2:-$HOME/ImperialismMac}"
[ -f "$src/Imperialism.exe" ] || { echo "usage: $0 <folder containing Imperialism.exe> [output folder]"; exit 1; }
command -v wine >/dev/null 2>&1 || command -v wine64 >/dev/null 2>&1 || { echo "wine not found: see docs/mac_ipad.md (brew tap gcenx/wine; brew install --cask --no-quarantine wine-stable)"; exit 1; }
WINE=$(command -v wine || command -v wine64)
case "$out" in "$(pwd)"/*) echo "refusing to write inside the current folder ($out); pick a place outside the repository"; exit 1;; esac

mkdir -p "$out"
echo "copying game files to $out/game (the original stays untouched) ..."
mkdir -p "$out/game"
cp -R "$src"/. "$out/game"/
mkdir -p "$out/game/Save"

echo "creating a 32-bit Wine prefix ..."
WINEPREFIX="$out/prefix" WINEARCH=win32 "$WINE" wineboot -i 2>/dev/null || \
  WINEPREFIX="$out/prefix" "$WINE" wineboot -i   # newer Wine builds are WoW64 only and refuse WINEARCH=win32

cat > "$out/play.sh" <<EOF
#!/bin/sh
# Start Imperialism under Wine.  "play.sh noshim" uses Wine's own display layer instead of the project's scaling shim.
cd "$out/game"
export WINEPREFIX="$out/prefix"
export WINEDEBUG=-all
if [ "\$1" = "noshim" ]; then
  export WINEDLLOVERRIDES="winmm=n,b;msvfw32=b"
else
  export WINEDLLOVERRIDES="winmm=n,b;msvfw32=n,b"
fi
exec "$WINE" Imperialism.exe
EOF
chmod +x "$out/play.sh"
echo "done. Start the game with: $out/play.sh   (or '$out/play.sh noshim' if the window is blank)"
