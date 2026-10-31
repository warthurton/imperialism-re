# Plan: lift all the game logic into clean, portable C

Goal: a `core/` library in plain C11 (no Windows headers, no MFC, no GDI) that contains every game rule: the state structs, the turn simulation, the AI, combat, and loading/saving
the game's own save files. A thin front end (SDL, later; see the port discussion in `docs/STATUS.md`) sits on top. The original exe is the specification; the reimplementation
must behave the same, and we prove it by comparing against the running game, not by hoping.

## Where we really are (measured with `tools/callgraph_stats.py`, 2026-10-31)

| | Functions | Lines of decompile |
|---|---|---|
| Whole decompile | 10,937 | ~458k |
| Library code (CRT, MFC, link stubs, framework, static init) | ~5,650 | ~190k |
| **Game code** (everything else) | **5,290** | **~267k** |
| of which has a Ghidra auto-name only (`FUN_xxxxxxxx`) | ~2,260 | |
| of which carries a structural name (`TClass_vfN`, derived from vtables) | ~2,930 | |
| of which has a **meaning** name assigned by us (`names/names.tsv`) | **~100** | |
| Reachable by *direct* calls from the turn driver `TSimMgr_AdvancePhase` | 216 | ~19k |

Reading these honestly:
* "Named" in the decompile mostly means *which class and vtable slot*, not *what it does*. Understanding is about 2% of the game code by count. The rules we decoded by playing
  (production, trade, transport, tech, diplomacy) are a few dozen functions plus their tables.
* Almost all the simulation hides behind **vtable calls** (`(**(code **)(*obj + 0x38))()`), which a static call graph cannot follow; that is why only 216 functions are "reachable".
  The real set is much larger. A static decompile alone will never tell us what runs.
* Playing the game taught us rules, but it does not measure coverage and it does not scale to the AI, combat and map code. The user is right that it is not, by itself, a path
  to a complete lift. It stays useful in exactly one role (below): as the **oracle** that proves a lifted function is right.

## The method: decompile is the source, the running game is the oracle, differential tests are the proof

1. **Know what runs (dynamic coverage).** Build a tracer that puts a breakpoint at the entry of every function (about 11k addresses, all known), logs the first hit, the hit count and the
   *actual* caller (return address) per phase of a turn, then removes the breakpoint. That resolves every vtable call, gives the true call tree of End Turn, and gives a coverage
   percentage to drive the work. Output: `results/coverage_<scenario>.tsv` (git-ignored) and a per-phase function list in `docs/`.
2. **Know the data (typed state).** Mine the decompile for every `*(T *)(obj + 0xNN)` access per class and per global (a script, `tools/field_miner.py`): offsets, widths, read/write
   counts, which functions touch them. Turn that into real C structs in `core/include/` (named fields, comments with confidence). Known so far: `TGame`, the Great Power and city
   objects, `TDiplomacyMgr` (four 23x23 matrices), `TTechMgr`, the map manager (6,480 tiles of 0x24 bytes), the trade tables.
3. **Snapshot oracle.** A tool that dumps the whole game state from memory (all the objects above, every manager) before and after an End Turn, plus the RNG seed. `core/` loads
   the "before" snapshot, runs the same turn, and `tools/diff_snapshot.py` compares field by field. The game is deterministic given its seed (a linear congruential generator,
   multiplier 0x15a4e35, seen in the tech scheduler), so a mismatch is a bug in our lift, with the offending field named. Fixtures (`saves/`) provide the starting situations;
   playing is how we reach rare situations (war, colony, a tech release) and record them.
4. **Lift bottom-up.** Leaves first (pure functions, tables, RNG, accessors), then managers, then phase handlers, then the AI. Each lifted function: clean C with the new
   struct types, a comment with the original address, a unit test fed from snapshots, and a row in `docs/REIMPL_STATUS.md` (function, address, state: traced / lifted / verified).
   LLM help is welcome for the first draft of a clean version (local models via `tools/ocr_pdf.py`'s Ollama setup, or this agent), but nothing counts as done until it passes the
   differential test.
5. **Keep the front end separate.** UI code (`ui_screens`, `ui_layouts`, `display`: about 2,800 functions) is *not* lifted line for line. We decode only what the front end must
   reproduce (screen flow, hit areas, text) from `docs/screens.md` and the text log, and write a new UI.

## Milestones

| | What | Done when |
|---|---|---|
| M0 | Tooling: coverage tracer, snapshot dump and diff, field miner | one End Turn traced; coverage and a snapshot pair saved for each fixture |
| M1 | Turn skeleton in `core/`: load a save into typed structs, run the 0x00-0x12 phases as no-ops, write the save back byte-identical | load, save, compare equal for all fixtures |
| M2 | Economy: production, transport, trade settlement, tech release and purchase, diplomacy overtures and the war ripple (the `reimpl/*.c` models, rewritten onto the real structs) | snapshot diff of an End Turn matches on economic fields |
| M3 | Population, map ownership, provinces, income and upkeep | matches on those fields over 20 turns |
| M4 | Great Power AI for diplomacy and trade (what the AIs offer and accept) | AI offers and scores match the oracle with the same seed |
| M5 | Military AI and combat (`military_ai`, the 1,100-function group; the tactical battle) | battle results match for recorded battles |
| M6 | Save compatibility in both directions; scenarios; difficulty levels | the original game loads our saves |
| M7 | A new front end (SDL) for desktop, then tablet | playable |

M0 to M2 are weeks of work and most of the value; M4 and M5 are the long tail (the AI is by far the largest group). I would not promise M5 until the tracer shows how
much code the AI really executes.

## What changes about how we work

* **Stop exploratory playing for its own sake** (the Empire-overture test is parked; `docs/STATUS.md` still lists it). Play only to (a) build a fixture that reaches a code path
  the tracer shows is not yet covered, (b) investigate a snapshot mismatch, (c) decode something the front end needs.
* **Every session ends with a number:** coverage %, functions lifted, differential tests passing.
* **Progress is tracked by function**, not by rule: `docs/REIMPL_STATUS.md` is generated from `names/names.tsv` plus the tracer output.
* Rules, tables and screens already decoded stay valuable: they are the first tests (recipes, prices, the tech schedule, diplomacy matrices, the Armory and card tables).

## Risks

* **Size**: about 267k lines of game decompile. Mitigation: dynamic coverage first, so we lift what runs and skip dead code and the UI.
* **Ghidra type errors**: some decompiled arithmetic is wrong (signedness, shifts). Mitigation: the oracle catches it; read the disassembly where a diff disagrees.
* **Hidden global state** (about 50 `DAT_` and `g_` globals seen so far): include them in the snapshot.
* **Legal**: the lift must contain no game assets and no verbatim decompiler output in git (the public-repo rule in `AGENTS.md`). Clean C written from understanding, with addresses in comments, is fine; the generated decompile stays local.

## First actions (in order)

1. `tools/callgraph_stats.py` (done): the baseline numbers above.
2. Write the breakpoint tracer (`tools/trace_calls.py`, Win32 debug API through ctypes; the game is 32-bit, the tool must run with a 32-bit-capable approach or use a small C helper built with the existing llvm-mingw i686 toolchain).
3. Write the snapshot dump (`tools/snapshot.py`) for the objects we already have layouts for, and the diff tool. Verify on the economic fields we know.
4. Run the tracer over one End Turn on `oil_plant_built` and publish the real call tree and coverage.
5. Start `core/` with M1.
