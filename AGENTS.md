# Imperialism RE

Agent instructions (single source for Claude Code, GitHub Copilot and other coding agents).

Public fan project (MIT): reverse engineering and display modernization for Imperialism (1997, GOG). Learning
exercise. NEVER commit game files, decompiler output, discs or third-party binaries (see .gitignore; vendor_untrusted/
is proprietary and local only). Check `git ls-files` for binaries before shipping.

## Workflow
- Work on `topic/<name>` branches with grouped commits, then `tools/ship.sh "title"` (PR, merge commit into main).
  Never commit to main directly. Commit trailer: Co-Authored-By trailer naming the AI assistant used, plus its session link if it provides one.
- Guesses live in `names/names.tsv` (addr|name|kind|confidence|note). Edit rows, don't delete; then
  `python -I tools/name_classes.py` regenerates imperialism_named.c. Confidence: confirmed | likely | guess.
- `python -I tools/find_calls.py <regex>...` lists functions whose body matches all regexes.

## Gotchas
- Write Python/PowerShell scripts with the Write tool, not inline heredocs (backslashes get mangled; `\a` becomes BEL).
- `python -I` ignores the script dir; scripts insert their own sys.path.
- `Remove-Item` on `C:\GOG ...` is blocked: build to a new filename and Move-Item.
- Shim build is 32-bit (llvm-mingw i686 clang): see shim/build.sh. Game DLLs are locked while it runs.
- Tests (harness/, Windows PowerShell 5.1): kill the game after every test; never leave it running.
- Vtable calls hide callers: search for `+ 0xNN))(` patterns, not function names.

## Where things are
README.md (layout, rebuild), docs/ (trade_rows.txt, turn_phases.md, recipes.md), classes.tsv, ghidra/, tools/,
shim/ (display), winmm/ (music DLL rebuild).
