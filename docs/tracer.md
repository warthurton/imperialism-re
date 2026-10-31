# The coverage tracer (`tools/tracer/`)

A static call graph cannot see the game's simulation because almost everything runs through vtable calls. The tracer attaches to the **running game** and records what actually executes.

## How it works

`trace_calls.c` (a 32-bit program, like the game; built with the i686 llvm-mingw clang) attaches as a debugger, writes an INT3 at the entry of every function in a list, and on each hit
records: the hit count, the order in which functions are first seen, the **caller** (the return address at the top of the stack, mapped to the function that contains it), and the
**turn phase** (every hit of the turn driver `TSimMgr_AdvancePhase` reads its `this+4` as the current phase, and later hits are tagged with it). After a function has been hit `--cap` times (default 100) its
breakpoint stays removed, so hot functions do not slow the game down. On the way out it restores every original byte and detaches, so the game keeps running.

* `tools/tracer/make_funclist.py` writes `results/funclist.txt` (4,868 functions from the game groups; library code, the framework group and the parked multiplayer/DirectPlay groups are left out).
* `trace_calls.exe <pid> results/funclist.txt results/<name> [--seconds N] [--cap N] [--phase-fn HEX]` writes `<name>_funcs.tsv` and `<name>_edges.tsv` (git-ignored).
* `tools/tracer/analyze_trace.py results/<name>` prints counts per phase, group and source file; `--phase N` lists a phase's functions in call order with their callers; `--unnamed GROUP` lists the hit functions that still
  have only an auto name, most called first; `--export file.tsv` writes the readable table (the one kept in `docs/trace_end_turn.tsv`).
* Build and run: `i686-w64-mingw32-clang -O2 -static -o results/trace_calls.exe tools/tracer/trace_calls.c`; start the game from a fixture (`harness/prod_boot.ps1 -Fixture oil_plant_built -Restart`), start the tracer on its pid in the
  background, drive the game (`harness/prod_endturn.ps1`), then create the file `results/<name>.stop` (or wait for `--seconds`).

## First result: one End Turn (fixture `oil_plant_built`, turn 5, offers rejected)

| | |
|---|---|
| Functions hit | **1,138** of 4,868 traced (static reachability from the turn driver had found 199) |
| Breakpoint hits / distinct call edges | 24,381 / 1,887 |
| Reproducible | a second, independent trace of another turn (turn 4 to 5, 1,132 functions) shares 1,113 functions (98.3%) with it |
| An idle game (mouse moves, nothing else) | 0 functions hit: everything above belongs to the turn and its screens |
| Simulation groups hit | `nations_sim` 212, `military_ai` 201, `production` 97, `map_sim` 41, `trade` 30, `name_gen` 10 (591 functions) |
| Interface groups hit | `display` 365, `ui_screens` 147, `ui_layouts` 32 |
| Still only an auto name among the simulation functions hit | 219 (`nations_sim` 81, `military_ai` 81, `map_sim` 41, `production` 11, `trade` 5): the decode queue |
| End Turn under the tracer | 15-24 s instead of 7 s (`prod_endturn.ps1` now waits for the turn to leave the map before judging it finished) |

The per-function table is `docs/trace_end_turn.tsv` (address, name, group, source file, hits, first-seen order, phase mask, first caller). Phase numbers seen: 5 to 25 (the driver has more phases than the 0x00-0x12 listed in `docs/turn_phases.md`),
plus 97 functions seen before the first phase tag (the End Turn button handler and screen switches).

## What it is good for

* **The decode queue**: `analyze_trace.py --unnamed nations_sim` (and the other simulation groups) gives the functions that run every turn and are still unnamed, busiest first.
* **Real call trees** with vtable calls resolved: `--phase N` shows who calls whom, in order.
* **A coverage number for the plan**: functions hit / functions in scope, per fixture and per scenario (a turn with a war, a tech release, a colony will hit more).
* **Evidence for the source-file boundaries**: functions that call each other in one phase and sit in an open zone can now be compared (not yet used).

## Detaching safely (a bug found and fixed on 2026-10-31)

The first version restored the breakpoints and detached while the game was running. A thread that executed a still-planted INT3 in that instant raised a breakpoint exception that nobody answered, and the game died
(Windows event `0x80000003` at `0x5b66b0`; the user saw "Imperialism is not responding"). The tracer now removes every breakpoint, marks all functions disabled, and keeps answering debug events (a breakpoint on one of its
addresses is resumed at the original instruction) until the game has been quiet for half a second, and only then detaches. `harness/trace_endturn.ps1 -Name x -StopAfterSeconds N` detaches N seconds into an End Turn as a stress test:
it survived stops at 1, 2, 5 and 8 seconds, and a normal turn afterwards.

Side effects to know about: a crashed game can leave a dead process that Windows keeps listed (`Get-Process` shows it with `HasExited = True`) while the desktop compositor holds a "(Not Responding)" ghost window for it.
The harness and the Python readers now ignore exited processes (`Where-Object { -not $_.HasExited }`), so they pick the live game. To clear a ghost: send it `WM_SYSCOMMAND` / `SC_CLOSE`, then press **End Process** in the
dialog that appears. Also: an interrupted End Turn can leave the game on a trade offer sheet (screen id 8500); the Escape key may not reach it, but clicking the red REJECT seal does.

## Limits

* Only function **entries** are traced, not returns or data; a function called through a table whose first byte is not an instruction start of the traced list is missed.
* A thread that runs through a function in the instant its first byte is restored for the single step is missed (rare; the game has few threads).
* One scenario covers one set of branches. Combat, colonies, a Great Power's collapse and the AI's war decisions need their own fixtures.
* The decompile's function list comes from Ghidra; if it merged or split a function, the entry is still the real address.
