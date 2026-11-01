# Display and music builds moved

The maintained display shim and music-wrapper build tooling now live in
[Imperialism Compat](https://github.com/warthurton/imperialism-compat).
It has its own source, native tests, Windows CI and source-inclusive packages.
The original display source history remains in this repository before the split.

This extraction was deliberate: Compat owns runtime display/music compatibility
and distributable releases; Imperialism RE owns decompilation, analysis, snapshots
and portable game-logic reimplementation. The local game harness belongs to RE
because it depends on RE fixtures and readers. See [../CHANGELOG.md](../CHANGELOG.md).

The RE repository links Compat at `compat/` as a Git submodule pinned to a specific
revision. Clone RE with `--recurse-submodules`, or run this from the RE root:

```sh
git submodule update --init compat
```

After pulling an RE revision that changes the pin, run that update command again.
The wrapper scripts use `compat/` by default; `IMPERIALISM_COMPAT` can select another
Compat checkout. `shim/build.sh` preserves the old display build entry point;
`winmm/build.sh` preserves the GOG-codec music build entry point. Neither installs
into the game directory automatically. Both music codec variants are available
through Compat's own scripts.

To update the pin, first merge and push the desired Compat changes in its own
repository. Fetch/check out that published revision inside `compat/`, validate it,
then commit the changed `compat` gitlink in an RE topic branch with its test evidence.
Avoid `git submodule update --remote` during normal builds: it follows a moving
branch rather than the revision recorded by RE.

The installed test DLLs and older ignored build outputs remain local. The
`archive_winmm_patch/` directory is historical research, not the current supported
music build. The RE harness remains here because its fixtures/readers belong to
the reverse-engineering project.

`harness/prod_compat.ps1 -Name compat_unique_name` temporarily installs the `compat/`
Compat builds, runs the snapshot turn test for each music variant, then restores
the original DLLs and INI files with hash checks and stops the game. Raw backups
and validation stay in ignored `results/trace_*` / `results/snapshot*` paths.
Pass `-CompatRoot <path>` to test another checkout explicitly.
