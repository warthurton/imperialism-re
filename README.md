# Imperialism (1997) – reverse engineering and modernization workspace

Work on the GOG install of *Imperialism* (`C:\GOG Games\Imperialism`): 32-bit MSVC 5 / MFC 4 / GDI-only game.
This repo holds our own code, tools and notes. It deliberately does **not** hold game files, decompiler output
or third-party binaries (see `.gitignore`); everything excluded can be regenerated with the scripts below.

## What is here

| Path | What |
|---|---|
| `shim/` | `shim.c`: proxy `msvfw32.dll`. Windowed scaling, resizing, F11 fullscreen on the brown backdrop, mouse mapping, blocks the game's self-minimize. `build.sh` builds it. `archive_winmm_patch/` = the retired runtime patcher for GOG's winmm.dll. |
| `winmm/` | `build.sh`: rebuilds the music DLL from the maintained open-source ogg-winmm (pinned commit), linked against the game's own libvorbisfile. |
| `tools/` | `patch_winmm_file.py` (binary-patches the three buffer races in GOG's stock winmm.dll; fallback if you keep GOG's DLL), class/vtable naming, string-table and resource dumpers. |
| `ghidra/` | Headless-Ghidra scripts (`ExportC` = full decompile, `CreateEntries` = create functions Ghidra missed, `ExportNew`). |
| `classes.tsv`, `renames.json` | The game's ~400 `T*` classes (size, base, factory) and the 3,167 virtual methods named from them. |
| `docs/` | Findings (trade table layout and price formulas, etc.). |
| `harness/` | Windows PowerShell 5.1 test harness that drives the real game (clicks, keys, screenshots, per-process audio meter, crash counting). `test18.ps1` = stress run, `test21.ps1` = music at each stage, `test22.ps1` = fullscreen look. |
| `results/` | Raw outputs of past test batches. |

## Rebuild / install

* Shim: `shim/build.sh build.dll`, then (game closed) copy over `msvfw32.dll` in the game folder.
* Music DLL: `winmm/build.sh "C:/GOG Games/Imperialism/libvorbisfile-3.dll"`, copy `winmm/build/winmm.dll` over the game's `winmm.dll`.
  Keep GOG's original (`original/winmm.dll`, not in git) to roll back.
* Decompile: `analyzeHeadless … -postScript ExportC.java <out.c>`; then `CreateEntries.java` with a list of vtable/factory
  entry points, `ExportNew.java`, and `tools/name_classes.py` to get `imperialism_named.c`.
* Crash dumps: HKLM `...\Windows Error Reporting\LocalDumps\Imperialism.exe` (full dumps into `dumps/`), open with lldb
  (`lldb -c <dump>`).

## Test-running rules

The game is killed after each test; nothing is left running. Screenshots capture only the game window. Saves are not
precious (user's word) but do not touch `Save\` deliberately.

## Notes

* `Remove-Item` on `C:\GOG ...` is blocked by a local guard; build to new filenames and `Move-Item` instead.
* Python run with `-I` ignores the script directory: scripts insert their own path.
* The shim and the music DLL are GPL-compatible work; ogg-winmm is GPLv2 (source in its repo at the pinned commit).
