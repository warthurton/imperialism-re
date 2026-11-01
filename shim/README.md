# Display and music builds moved

The maintained display shim and music-wrapper build tooling now live in
[Imperialism Compat](https://github.com/warthurton/imperialism-compat).
It has its own source, native tests, Windows CI and source-inclusive packages.
The original display source history remains in this repository before the split.

Clone the two repositories beside each other, or set `IMPERIALISM_COMPAT` to the
Compat checkout. `shim/build.sh` preserves the old display build entry point;
`winmm/build.sh` preserves the GOG-codec music build entry point. Neither installs
into the game directory automatically. Both music codec variants are available
through Compat's own scripts.

The installed test DLLs and older ignored build outputs remain local. The
`archive_winmm_patch/` directory is historical research, not the current supported
music build. The RE harness remains here because its fixtures/readers belong to
the reverse-engineering project.

`harness/prod_compat.ps1 -Name compat_unique_name` temporarily installs the sibling
Compat builds, runs the snapshot turn test for each music variant, then restores
the original DLLs and INI files with hash checks and stops the game. Raw backups
and validation stay in ignored `results/trace_*` / `results/snapshot*` paths.
