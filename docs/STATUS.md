# Status: where the project stands

Update this file at every ship (and before ending a session). It is the first thing to read after `AGENTS.md`.
Last updated: 2026-10-31 (military snapshot graph, planning probe and later-turn fixture; game stopped after each test).

## Done and verified (in the running game unless noted)

- **Snapshot oracle, partial** (`docs/snapshots.md`, `tools/snapshot.py`, `tools/diff_snapshot.py`):
  read-only capture of game/nations/cities/orders/population, diplomacy, technology, trade/deals,
  map tiles/provinces, minister lists, military rosters/units/stacks, ships and both RNG states. Semantic and raw-byte comparison. The single-session
  `harness/prod_snapshot.ps1` checks idle identity, one completed turn, and byte agreement with
  the existing city/tech/diplomacy readers before and after, plus military-root agreement.
  Seventeen offline snapshot tests pass. Later-turn captures matched 517 units through
  province/stack and national-roster roots; the saved fixture reloaded and passed ten live checks.
- **Field miner, heuristic** (`tools/field_miner.py`, `docs/field_miner.md`): 8,779 functions
  analyzed, 8,702 candidate rows; unresolved scaling, nested pointer targets and dynamic indices
  stay separate. Counts and declaration-bound checks guide review, not automatic struct creation.
  Eleven miner tests pass. City task/auxiliary containers added to snapshots after code/disassembly
  review; live empty-container validation passed (nonempty traversal is synthetic-tested only).
- **City planning probe** (`tools/tracer/city_planning.txt`, `harness/trace_city_planning.ps1`):
  one measured turn after eight warmups hit the minister turn entry and vf33, but none of
  the selected city-task producers/consumer. Populated minister raw lists are not evidence
  of populated city task queues. The latter remain live-unverified (`docs/tracer.md`).
- **Display shim** (`shim/`): windowed scaling, maximize, fullscreen with integer scale, mouse mapping, and an opt-in **text log** (installed build: `shim/build20.dll`;
  the previous one is `original/msvfw32_before_textlog.dll`). The game's music-loss crash is intermittent and **not proven fixed** (`winmm/` rebuilt from ogg-winmm).
- **Decompile**: 10.9k functions named; `src/` groups (git-ignored) from `tools/split_source.py`, none left unsorted (the `late`/`laddr` rows are filing guesses,
  audited with `tools/audit_groups.py`); big functions via `ghidra/Probe.java` (Board of Trade builder 0x4601b0 = `TScreenBuilder_BoardOfTrade`).
- **Turn flow**: `CompleteOrders` runs in phase 8 for every locally simulated power, human included; `BeginTurn` is phase 0x12; diplomacy overtures are executed in the
  diplomacy phase by `TDiplomacyMgr_ExecuteOvertures` (`docs/turn_phases.md`, `docs/how_a_turn_works.md`).
- **Production** (`docs/production_playtest.md`, model `reimpl/production.c`, self-tested): all recipes, shortages, training, units, Food, capacity, **Power Plant**
  (build $5,000, 1 Fuel = 6 power, **no 100-fuel cap**: 150 Fuel = 900 power, a standing order survives running out of Fuel), **Refinery** (build 2 Lumber + 2 Steel,
  expand +2 for 2 + 2, both cancels refund). Oil-age sites exist only when the local power's tech-19 record in `TTechMgr` is 2 (the local power's index changes per game).
- **Diplomacy** (`docs/diplomacy.md`, model `reimpl/diplomacy.c`, self-tested): four 23x23 matrices (relation, status, turn stamp, presence 0/1/2 = none/consulate/embassy);
  status names from game strings (4 Peace, 3 Pact, 6 War ...); overture ids in the Great Power's pending table at +0xb2 (War 0x131, Consulate 0x133, Embassy 0x134,
  Alliance 0x12e, Pact 0x12f, Peace 0x130); costs ($500 / $5,000 at once); Pact and Peace effects; **the war ripple** (`TDiplomacyMgr_ApplyWarFallout`, predicted a second war
  cell for cell); relationship colour code; aid and minor-favourites rules (code only).
- **Test harness** (`harness/`): `prod_boot.ps1` loads a save from the title screen in ~11 s; `prod_do.ps1` chains clicks, hot-key screen changes (`go ...`), dialog steps from
  the dialog's real window rect (`dplus dat dok dcancel dexpand ...`), `mark`/`txt` to READ the text the game drew; `prod_endturn.ps1` ends a turn in ~7 s by screen id
  (offer sheet 8500 Esc, results 8800 and Imperial Times 8451 Return). Memory readers (read-only): `tools/readcity.py`, `readview.py id`, `readtech.py`, `readprefs.py`,
  `readdiplo.py`, `readnations.py`, `readpending.py`, `readtext.py`; `predict_war.py`. Writers (fixtures only): `poke_stock.py`, `poke_tech.py L:19`.
  Screens, ids, the main menu and reading text: `docs/screens.md`.
- **University, Transport, Trade** (`docs/production_playtest.md` end, `docs/transport.md`, `docs/trade.md`; models `reimpl/production.c`, `transport.c`, `trade.c`, self-tested): civilians cost
  1 expert + 2 Paper + cash ($500 Prospector ... $2,000 Engineer), charged at once, reported next turn; the Transport sliders and capacity bar; the Board of Trade (4 bids max, settlement in
  board order, **merchant marine 16 units limits sales plus purchases**, bottom line = cash change).
- **Armory and Indiaman** (`docs/production_playtest.md`, `reimpl/production.c`): eight regiments with costs read from the dialog; Cuirassier + Sapper ordered for real and charged as modelled; Indiaman 3 Fabric + 7 Lumber, merchant capacity +4.
- **Fixtures** (`saves/README.md`): `oil_t0`, `oil_refinery4`, `oil_plant_built` (turn 4, plant built, Refinery 4),
  `military_later` (city turn 13/game turn 14, 517 units, one ship) and the earlier production ones.

## Open questions

- **Diplomacy leftovers**: the Empire overture (id 0x12d is a guess; not offered at the relationship tried; the manual and the card say it needs an Embassy and friendly relations, so try it where an Embassy exists: `docs/card_tables.md`), what an Alliance does on the Great Power side (Kem did not ally), foreign aid
  in play (Grants tab; table at Great Power +0xe0), the peace version of the fallout routine, status codes 0, 1 and 5. The Offer Sheet's settlement logic (`TTradeMgr_SettleTrades`) is read, not tested.
- **Dialog identity**: a dialog's size gives its kind (production 276x149, construction 320x320) but not which building it belongs to (the text log can now tell: read the dialog's strings).
- **Quick reference card** (`docs/card_tables.md`, read by eye; the manual in `docs/manual/` is git-ignored and rebuilt by `tools/ocr_pdf.py`, see `docs/manual_ocr.md`): terrain and levels, unit stats for three eras and the navy, the diplomacy chart; matches the Armory, Shipyard and recipes seen in play.
- **Technology**: `docs/technology.md`. The microscope and hot key 5 are the same screen; buying is one click, $ charged at once, "Purchasing" then "Purchased in <year>". Techs are released by the calendar (random turn inside a window per tech, tools/dump_techtable.py); prices are a fixed table. Open: the other techs' effects, AI buying.
- Briefings through the registry survive a loaded save but not a new game; the Library and Load screens have no found way out except choosing.
- `names/names.tsv`: 0x4357b0 is now `TScreenBuilder_HelpAndSmallWindows` (likely: a switch on window id building the Help topics/tips window and other small windows; read from code, not seen in play). The 8 unnamed map-reading functions at 0x557e10-0x55a160 and 0x563990 moved from `ui_screens` to `military_ai` (they read `g_MapMgr` and sit among TPortZone/TOcean code; `names/groups.tsv`). `map_sim`, `display` and a few `nations_sim` placements near 0x5149d0 are still guesses.
- Slider quirk: clicking the slider track jumps proportionally and the right arrow adds one step; dragging the knob did not move it.

- **Technology purchase** seen in play (Cotton Gin $1,000), `docs/technology.md`.
- **Mac/iPad**: `docs/mac_ipad.md` and `tools/mac/make_wrapper.sh` (private Wine wrapper on a Mac, then stream or emulate to the iPad). Written without a Mac: untested, fix as you go.

## Handoff: where the lift stands (written 2026-10-31, for the next agent)

**Goal** (`docs/PLAN_reimplementation.md`): lift all single-player game logic into clean portable C (`core/`), proving each piece by differential tests against the running game. Multiplayer and DirectPlay are tabled.

**Done and merged**
* Tracer (`tools/tracer/`, `docs/tracer.md`): attaches to the game, finds which of 4,868 functions run. First clean result: one End Turn = 1,138 functions, 591 simulation, 219 of those unnamed. Table: `docs/trace_end_turn.tsv`.
* Source files recovered from the exe's assert strings (`docs/source_tree.md`, `names/source_attribution.tsv`: assert 198, inferred 1,031, cut 243, prior 1,503, open 2,631), `Ambit_Assert` named, map code re-filed, multiplayer parked.
* Verified rules with tested models in `reimpl/`: production, Armory, Shipyard, University, transport, trade, tech release (`docs/technology.md`, `reimpl/tech.c`), diplomacy. Card tables in `docs/card_tables.md`.
* OCR tool for the manual/card (`docs/manual_ocr.md`, git-ignored output in `docs/manual/`), Mac/iPad notes (`docs/mac_ipad.md`, untested), LF/CRLF rules, the quoting rule in `AGENTS.md`.

**Next, in order**
Snapshot continuation (2026-10-31): the partial schema-1 oracle now has successful live
before/idle/after captures from `oil_plant_built`. Keeping the whole test in one harness lifetime
avoided the earlier missing-process failure; its exact cause remains unproven. Expanded run
`snapshot_live2` passed eight checks: 490 -> 498 blocks, 3,932 decoded fields, 266 field changes
across 188 blocks. Final run with both RNG states (`snapshot_live3`) also passed all eight:
491 -> 489 blocks, 3,933 fields, 282 changed fields across 173 blocks. Idle bytes identical,
game turn 5 -> 6, local cash $44,400 -> $44,250; game stopped and settings restored.
Field-miner continuation: heuristic index implemented (`docs/field_miner.md`), including
pointer scaling, cast order, nested targets, dynamic indices, read/write counts and bounds.
It exposed city +0x270/+0x274 containers. The task-list embedded header needed a +4 adjustment,
confirmed in machine code after the first live read rejected it. Corrected `snapshot_fields2`
passed all eight checks: 505 -> 507 blocks, 3,947 decoded fields, 269 changes across 173 blocks;
idle bytes identical. The containers were empty: populated traversal remains live-unverified.
That revision passed eleven miner tests and ten snapshot tests.

Military continuation: `tools/snapshot_graph.py` captures the Interior Minister (nation +0x98,
not Foreign at +0x94), its list headers/nodes, Army Manager records/grouped stacks, direct
province unit chains, all 23 national military rosters, Navy Manager and global ship chain.
Province +0x98 points to TMilitaryUnit directly, not TArmyStack. Constructor/save/load
evidence and bounds are in `docs/snapshots.md`. Raw minister node values are not dereferenced.
`snapshot_planning2` passed ten checks after eight warmups: game turn 13 -> 14, 4,125 decoded
fields, 1,918 -> 1,901 blocks, 238 changed fields across 225 blocks. Its 517 units matched
the independent roster roots; no listed/placed discrepancies, one ship. Idle bytes identical.
The 15-entry planning trace hit only BeginTurn (6), vf33 (6) and the phase driver (17).
City task/auxiliary queues and the minister +0x18c list remained empty; army record/grouped-stack
lists were also empty. Nonempty versions of those containers are synthetic-tested only.
Saved `military_later.imp`; reload (`snapshot_fixture_later1`) passed ten checks at game turn
14 -> 15, 1,901 -> 1,937 blocks, 262 changed fields across 241 blocks, again with 517 units
before the turn and one ship. Seventeen snapshot and eleven miner tests pass. No functions lifted.
All game sessions ended with settings restored, including the rejected trace harness exit-code
check (fixed by retaining its process handle before exit). M0 is not complete; raw snapshots
and traces remain local and ignored.
Next: remaining naval task-force/port/mission and province/nation pointer targets; inspect
city-task producer callers to select a scenario that actually exercises them; snapshot pairs
for the remaining fixtures and replay checks. Do not repeat warmup-only tests as proof of task coverage.

1. **Expand snapshot coverage** (`tools/snapshot.py` + diff, partial capture validated): remaining pointer targets and managers, then pairs for more fixtures. Use `tools/field_miner.py` to find candidate layouts and check them against constructors/save methods/disassembly. See `docs/snapshots.md` and `docs/field_miner.md` for bounds, evidence and current limits.
2. **Decode the 219 unnamed simulation functions** the trace hit: `python -I tools/tracer/analyze_trace.py results/trace4 --unnamed nations_sim` (and `military_ai`, `map_sim`, `production`, `trade`); `--phase N` lists a phase in call order with callers. Name them in `names/names.tsv` with evidence.
3. **More trace scenarios**: a war, a tech release (`tools/poke_techturn.py`), accepted offers (`prod_endturn.ps1 -Accept`), an Empire/colony turn, an AI-heavy later turn. Save fixtures with `harness/prod_save.ps1`.
4. Narrow the 2,631 open source-file functions using trace evidence (functions that run together in one phase), then start `core/` M1 (load a save into typed structs, write it back byte-identical).

**How to run a trace** (all local, nothing is committed): `python -I tools/split_source.py` (writes `src/`, needs the local decompile), `python -I tools/tracer/make_funclist.py`, build with `i686-w64-mingw32-clang -O2 -Wall -static -o results/trace_calls.exe tools/tracer/trace_calls.c`
(the compiler is in scoop's `mingw-mstorsjo-llvm-ucrt`), `harness/prod_boot.ps1 -Fixture oil_plant_built -Restart`, then `harness/trace_endturn.ps1 -Name <new name>`, then `python -I tools/tracer/analyze_trace.py results/<name>`. End with `harness/prod_end.ps1`.

**Gotchas learned the hard way**
* **Never put multi-line text through the shell** (heredocs, `python -c`, long `-m`): use the Edit and Write tools, script files, `git commit -F`, and `sh tools/ship.sh "title" <body file>` (see `AGENTS.md`, Quoting rule).
* `Remove-Item` on `C:\GOG ...` is blocked: use a new file name (the tracer now deletes a stale `<name>.stop` itself).
* A crashed game can leave a dead process that Windows keeps listed (`HasExited = True`) with a "(Not Responding)" ghost window; the harness and readers ignore exited processes now. To clear the ghost: send `WM_SYSCOMMAND` `SC_CLOSE` to it, then press End Process in the dialog.
* An interrupted End Turn leaves the game on a trade offer sheet (screen 8500); Escape may not reach it, clicking the red REJECT seal does; `prod_endturn.ps1` now also resumes from 8500/8800/8451.
* Do not run two copies of the game; always `prod_end.ps1` at the end; `python` needs plain `python` (not `-I`) only for `tools/ocr_pdf.py` (PyMuPDF in the user site).
* Branch workflow: `git switch -c topic/<name>`, grouped commits, `tools/ship.sh`; it leaves you on `main`.

## Next steps (suggested order)

0. **The direction is now `docs/PLAN_reimplementation.md`**: lift all game logic into clean portable C, with a breakpoint tracer for real coverage, typed state structs, and a snapshot diff against the
   running game as the proof. First actions: the tracer, the snapshot dump and diff, the field miner. Exploratory playing is parked (the items below stay as open questions, not as the plan);
   baseline numbers come from `tools/callgraph_stats.py` (216 of 5,290 game functions reachable by direct calls from the turn driver; about 100 have a meaning name).
   **New: the original source file names are in the exe** (assert strings, `docs/source_tree.md`): about 45 files (`UCity`, `UCountry`, `UCountryAuto`, `UArmyMgr`, `UNavy`, `UOcean`, `UMissionSubs`, `UTacPlayer`, `UUnit`, `UMap`, `UMapper`, ...),
   used as the module structure for the plan; `UMap`/`UMapper` re-filed to `map_sim`; `Ambit_Assert` named. Boundary zones narrowed by `tools/source_boundaries.py` (class and stub-order evidence, plus a labelled semantic prior):
   2,631 functions still open. **Coverage tracer built** (`docs/tracer.md`, `tools/tracer/`): one End Turn runs 1,138 functions, 591 of them simulation code (219 unnamed: `analyze_trace.py --unnamed GROUP` is the decode queue; two independent traces agree on 98.3%). **Multiplayer is tabled** (groups `multiplayer` 262 and `directplay` 149 are parked and not counted: `docs/PLAN_reimplementation.md`).
1. Done: University/Trade School, Transport, trade settlement, Shipyard, Armory, Indiaman. Left: the first-in-line rule and price formula (code notes in `docs/trade.md`; needs a Board of Trade
   with rival bids, so a fixture with more goods), and the full transport bar (unreachable with only food on the network: sliders stop at 'available', 10 of 15). Hussars $100 vs Skirmishers $200 not re-ordered.
2. Diplomacy leftovers above (order Empire where it is offered, ally with a Great Power, make a grant) if wanted.
3. Keep playing normally now and then with crash dumps armed (`dumps/`) to confirm the music fix.

## How to resume in a new session

1. Read `AGENTS.md`, this file, `docs/screens.md`, and the ends of `docs/production_playtest.md` and `docs/diplomacy.md`.
2. `git switch -c topic/<name>` (never commit on main), then `harness/prod_boot.ps1 -Fixture oil_plant_built -Restart` for a game to poke at.
3. Read screens with `prod_do.ps1 "mark; <action>; txt"` before taking a screenshot; end every game session with `harness/prod_end.ps1`.
