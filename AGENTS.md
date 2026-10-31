# Imperialism RE

Agent instructions (single source for Claude Code, GitHub Copilot and other coding agents).

**Start of every session: read this file, then `docs/STATUS.md`** (what is done, what is open, what to do next, how to resume). Follow its links to the other docs (see "Where things are" at the end).

Public fan project (MIT): reverse engineering and display modernization for Imperialism (1997, GOG). Learning
exercise. NEVER commit game files, decompiler output, discs or third-party binaries (see .gitignore; vendor_untrusted/
is proprietary and local only). Check `git ls-files` for binaries before shipping. Raw memory dumps (`results/*.bin`) stay
local. Saved games in `saves/` are fine (written by the game from a random world, no code or assets).

## Workflow
- Work on `topic/<name>` branches with grouped commits, then `tools/ship.sh "title"` (PR, merge commit into main).
  Never commit to main directly. Commit trailer: Co-Authored-By trailer naming the AI assistant used, plus its session link if it provides one.
- `ship.sh` leaves you on `main`: run `git branch --show-current` before every commit and start the next topic branch first.
- Guesses live in `names/names.tsv` (addr|name|kind|confidence|note). Edit rows, don't delete; then
  `python -I tools/name_classes.py` regenerates imperialism_named.c. Confidence: confirmed | likely | guess.
  Check the diff: rows can share identical text, so a blind replace can land on the wrong function.
- `python -I tools/find_calls.py <regex>...` lists functions whose body matches all regexes.
- **Keep `docs/STATUS.md` current** (done, open questions, next steps, how to resume): update it in the same PR whenever something is
  verified, found open, or finished, and before ending a session. Notes that live only in a conversation are lost.
- Say what is confirmed (seen in the running game or in the code) and what is a guess, in docs and commit messages.
- Verified rules go three places: a table in `docs/production_playtest.md` (step / seen / notes), the self-checking model
  `reimpl/production.c` (build and run it; it must keep passing), and the confidence column in `docs/recipes.md`.

## Gotchas
- **Quoting rule (agents keep breaking this): no text goes through the shell.** Never put multi-line text, a script, a commit message or a PR body inside a Bash/PowerShell command
  (heredocs, `python -c`, `python - <<EOF`, `echo "..."`, long `-m "..."`). Quotes, backslashes, `$`, backticks and apostrophes break them (`\a` becomes BEL, `\n` a real newline, an
  apostrophe ends the string, the whole command fails to parse and nothing runs). Instead: (1) change a file's text with the **Edit** tool (exact old string -> new string) or **Write** a whole new file;
  (2) for anything scripted, **Write** a `.py`/`.sh` file (in the scratchpad if it is throwaway) and run it with a short command like `python path/to/script.py`; (3) commit with
  `git commit -F <message file>` (Write the message first, trailers included) and ship with `sh tools/ship.sh "one-line title" <body file>`; (4) the shell only gets short single-line commands
  with simple arguments (paths, flags). If a `python` one-liner is truly unavoidable keep it free of quotes and backslashes, or use `chr(92)`, `chr(13)`, `chr(10)`.
- Line endings: `.gitattributes` and `.editorconfig` make everything LF except Windows-centric files (`.ps1`, `.bat`, `.cmd`, `.def`, `.ini`, `.ini.example`, ...), which are CRLF in the working tree;
  the repository stores LF for all of them, and the rules override `core.autocrlf`. The Edit tool keeps a file's existing line endings. Check with `git ls-files --eol` (every row should read `i/lf`,
  and `w/lf` or `w/crlf` for the Windows-centric ones); `git diff --stat` must not show whole-file noise.
- `python -I` ignores the script dir; scripts insert their own sys.path. Regexes over function bodies can backtrack
  catastrophically: prefer line-by-line checks.
- `Remove-Item` on `C:\GOG ...` is blocked: build to a new filename and Move-Item.
- Shim build is 32-bit (llvm-mingw i686 clang): see shim/build.sh. Game DLLs are locked while it runs.
- Vtable calls hide callers: search for `+ 0xNN))(` patterns, not function names. A call through an array
  (`(**(code **)(*(int *)*puVar3 + 200))()`) looks different from one through a named local.
- Read the game's manual: `pdftotext -layout "C:\GOG Games\Imperialism\Imperialism - manual.pdf" out.txt`. It names every screen,
  button and hot key (summary in `docs/screens.md`).

## Testing in the real game (harness/, Windows PowerShell 5.1: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...`)
- **Start from a save, not a new game.** `prod_boot.ps1 -Fixture <name> -Restart` writes the registry settings, launches, and
  loads the fixture from the title screen (Ship in the Bottle, slot 0, Load Game) in about 11 s. Fixtures are listed in
  `saves/README.md`; add one with `prod_save.ps1 <file> "<slot name>"` whenever a situation took many steps to reach. Use
  `prod_nav.ps1` (new game) only when no fixture fits.
- **Drive the UI with `prod_do.ps1`**, e.g. `"go industry; m 1000 400; w 0.3; plant; dplus 2; dclose; go map"`. `go
  transport|industry|trade|diplomacy|tech|map` uses the manual's hot keys; `endturn` plays through the turn. Dialog steps
  (`dlg dwait dplus dminus dend dclose dok dcancel dexpand`) use the dialog's real window rect, so never hardcode dialog
  coordinates (a dialog opens at a different place for each site). After entering a screen, move the mouse once before clicking a hotspot.
- **Read state from memory, not pixels.** `tools/readcity.py` (stock, capacity, labor, cash, orders), `readview.py id` (current
  screen id; table in `docs/screens.md`), `readtech.py`, `readprefs.py` are read-only. `poke_stock.py` and `poke_tech.py` write and
  are test fixtures only: orders must still be placed through the real UI so the game's own code runs, and the docs must say
  what was poked. `poke_tech.py L:19` targets the local power: its index (g_Game+0x2e) changes between new games, never hardcode it.
  Dialogs are `AmbitMcWindow` children of the game frame (`prod_wins.ps1`, `Get-Dialog`), not game objects.
- **Read the screen's text, do not look at it.** The shim logs every string the game draws (`TextOutA`, `ExtTextOutA`, `TabbedTextOutA`, `DrawTextA`) to
  `imperialism_text.log` when `[text_log] enabled=1` is in the game's `imperialism_shim.ini` (`prod_boot.ps1` sets it; needs the shim build with the text log,
  `shim/build.sh`). `prod_do.ps1 "mark; <action>; txt"` prints the text drawn in response (hot text, offer sheets, prices); `tools/readtext.py tail|since`. Strings come
  twice (shadow); the reader collapses them. Use this before a screenshot.
- **Keys go as window messages** (`Post-Key` in `fast.ps1`); a global `keybd_event` press stopped reaching the game. Escape rejects
  a trade offer, Return accepts or moves past results and the newspaper. Waits poll the screen id or the screen itself
  (`Wait-Stable`), not fixed sleeps.
- Quiet by default: `prod_vol.ps1 -Mode test` sets effects 10% and music about 5% and turns warnings and briefings off in the
  registry (a loaded save keeps them; a new game resets briefings to On). The idle-dock watcher is off (it shrinks the window and
  breaks hover scans). Do not run two copies of the game.
- **Always finish with `prod_end.ps1`**: it kills the game and restores the user's settings (effects 100%, music 75%, briefings and
  warnings On). Never leave the game running; screenshots capture only the game window (`shot.ps1`).
- Look at the manual and `docs/screens.md` before guessing what a screen or button does.

## Decompile pipeline
- Ghidra batch export gives up on a function after 60 s: `ghidra/Probe.java <addr> <out> <timeout>` (via analyzeHeadless
  `-process -noanalysis -postScript`) decompiles one big function; paste the result into `imperialism_decomp_extra.c`.
- `tools/split_source.py` writes the git-ignored `src/<group>.c`; `names/groups.tsv` rows: `name`/`body` (first match), `addr`
  (explicit range), `late` and `laddr` (last-resort heuristics for functions nothing else placed: treat the group as a filing
  guess). Run `tools/audit_groups.py` after changing them.

## Where things are
Read first: this file, then **`docs/STATUS.md`** (state, open questions, next steps, how to resume). Keep both current (see Workflow).
- `README.md`: layout and rebuild.
- `docs/snapshots.md`: partial read-only state capture, semantic/raw diff, coverage limits and validation.
- `docs/screens.md`: manual-based screen names, ids, main menu, hot keys, reading on-screen text. `docs/turn_phases.md`, `docs/how_a_turn_works.md`: the turn.
- Verified game rules, each with a tested model in `reimpl/`:
  `docs/production_playtest.md` + `docs/recipes.md` (production, Power Plant, Refinery, University, Shipyard; `reimpl/production.c`),
  `docs/diplomacy.md` (`reimpl/diplomacy.c`), `docs/transport.md` (`reimpl/transport.c`), `docs/trade.md` + `docs/trade_rows.txt` (`reimpl/trade.c`).
- `saves/` (fixtures, `saves/README.md`), `harness/` (game driving), `tools/` (readers, pokes, decompile tooling), `names/`, `classes.tsv`, `ghidra/`,
  `shim/` (display and text log), `winmm/` (music DLL rebuild).
- A new doc or model goes in this list in the same PR.
