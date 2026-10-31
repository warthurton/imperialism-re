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
| Functions hit | **1,132** of 4,868 traced (static reachability from the turn driver had found 199) |
| Breakpoint hits / distinct call edges | 25,874 / 1,831 |
| An idle game (mouse moves, nothing else) | 0 functions hit: everything above belongs to the turn and its screens |
| Simulation groups hit | `nations_sim` 216, `military_ai` 202, `production` 94, `map_sim` 37, `trade` 30, `name_gen` 10 (589 functions) |
| Interface groups hit | `display` 363, `ui_screens` 145, `ui_layouts` 32 |
| Still only an auto name among the simulation functions hit | about 220 (`nations_sim` 85, `military_ai` 79, `map_sim` 37, `production` 13, `trade` 5): the decode queue |
| End Turn under the tracer | 15 s instead of 7 s |

The per-function table is `docs/trace_end_turn.tsv` (address, name, group, source file, hits, first-seen order, phase mask, first caller). Phase numbers seen: 5 to 25 (the driver has more phases than the 0x00-0x12 listed in `docs/turn_phases.md`),
plus 97 functions seen before the first phase tag (the End Turn button handler and screen switches).

## What it is good for

* **The decode queue**: `analyze_trace.py --unnamed nations_sim` (and the other simulation groups) gives the functions that run every turn and are still unnamed, busiest first.
* **Real call trees** with vtable calls resolved: `--phase N` shows who calls whom, in order.
* **A coverage number for the plan**: functions hit / functions in scope, per fixture and per scenario (a turn with a war, a tech release, a colony will hit more).
* **Evidence for the source-file boundaries**: functions that call each other in one phase and sit in an open zone can now be compared (not yet used).

## Limits

* Only function **entries** are traced, not returns or data; a function called through a table whose first byte is not an instruction start of the traced list is missed.
* A thread that runs through a function in the instant its first byte is restored for the single step is missed (rare; the game has few threads).
* One scenario covers one set of branches. Combat, colonies, a Great Power's collapse and the AI's war decisions need their own fixtures.
* The decompile's function list comes from Ghidra; if it merged or split a function, the entry is still the real address.
