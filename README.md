# Imperialism (1997) – reverse engineering and modernization workspace

An unofficial, non-commercial fan project. I did it for three reasons: I like the game, I could not find anything like
it already out there, and it is a learning exercise in decompilation and reverse engineering.

**This repository contains no game files.** No executables, assets, data files, music, decompiler output or
third-party binaries are included. You need your own legal copy of the game (the notes here target the GOG release).
Everything excluded can be regenerated from your copy with the scripts below. The project is not affiliated with or
endorsed by the rights holders of *Imperialism*; the name belongs to them. If a rights holder objects to anything here,
open an issue and it will be removed.

What is here is original work: a display shim, build scripts, analysis tooling, and notes on how the game works
(trade, turn phases, class layout), with every guess marked by a confidence level in `names/names.tsv`.

This repo holds our own code, tools and notes. It deliberately does **not** hold game files, decompiler output
or third-party binaries (see `.gitignore`); everything excluded can be regenerated with the scripts below.

## What is here

| Path | What |
|---|---|
| `shim/` | `shim.c`: proxy `msvfw32.dll`. Windowed scaling, resizing, F11 fullscreen on the brown backdrop, mouse mapping, blocks the game's self-minimize. `build.sh` builds it. `archive_winmm_patch/` = the retired runtime patcher for GOG's winmm.dll. |
| `winmm/` | `build.sh`: rebuilds the music DLL from the maintained open-source ogg-winmm (pinned commit), linked against the game's own libvorbisfile. |
| `tools/` | `patch_winmm_file.py` (binary-patches the three buffer races in GOG's stock winmm.dll; fallback if you keep GOG's DLL), class/vtable naming, string-table and resource dumpers. |
| `ghidra/` | Headless-Ghidra scripts (`ExportC` = full decompile, `CreateEntries` = create functions Ghidra missed, `ExportNew`). |
| `lib_matches.tsv`, `lib_names.json` | MFC 4.21 and C-runtime functions found in the exe by matching the original static libs (`tools/match_lib.py` + `apply_lib_names.py`): 1,183 named. Needs the VC++ 5.0 disc (see below). |
| `classes.tsv`, `renames.json` | The game's ~400 `T*` classes (size, base, factory) and the 3,167 virtual methods named from them. |
| `docs/` | Findings: `how_a_turn_works.md` (start here), `turn_phases.md`, `recipes.md`, `trade_rows.txt`. |
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

## Reference material (not in git)

`vendor_untrusted/` (git-ignored, proprietary, from archive.org images of discs the owner holds): Visual C++ 5.0 Enterprise CD3
(`VSENT_CD3_Visual_C_5.0.iso`, md5 5bca897ceda88e2267d40cb2f0d49f4c) extracted to `vc50-extracted/` (MFC 4.21 source, headers,
`NAFXCW.LIB`, `LIBC.LIB`), and Visual Studio 97 SP3 (`vs97-sp3`, md5 afdd3e3a9089a7a9f6396f9f628cf4de). The original RTM libs match
the game better than SP3's (2,122 vs 2,018 functions), so the game was built with them. Regenerate the library names with:

    D=vendor_untrusted/vc50-extracted/DEVSTUDIO/VC
    python -I tools/match_lib.py $D/MFC/LIB/NAFXCW.LIB $D/LIB/LIBC.LIB
    python -I tools/apply_lib_names.py && python -I tools/name_classes.py

## Contributing / workflow

Work happens on `topic/*` branches with several commits grouped per topic. `tools/ship.sh "title"` pushes the branch and
opens a pull request that auto-merges into `main` (merge commit, branch deleted afterwards).

## Grouped source (local only)

`python tools/split_source.py` splits the decompiled `imperialism_named.c` into `src/<group>.c` (display, production,
trade, mfc, crt, ...) using the rules in `names/groups.tsv`. Name rules go first, then a body rule (GDI calls = display),
then unnamed functions sitting between two functions of the same group by address join that group. `src/` is git-ignored
because it is derived from the game; only the rules and the script are tracked. Edit `groups.tsv` and rerun to regroup.
