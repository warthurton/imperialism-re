# Status: where the project stands

Update this file at every ship (and before ending a session). It is the first thing to read after `AGENTS.md`.
Last updated: 2026-10-31 (Armory and Indiaman verified, 0x4357b0 named, a group placement fixed; game stopped).

## Done and verified (in the running game unless noted)

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
- **Fixtures** (`saves/README.md`): `oil_t0`, `oil_refinery4`, `oil_plant_built` (turn 4, plant built, Refinery 4) and the earlier production ones.

## Open questions

- **Diplomacy leftovers**: the Empire overture (id 0x12d is a guess; not offered at the relationship tried), what an Alliance does on the Great Power side (Kem did not ally), foreign aid
  in play (Grants tab; table at Great Power +0xe0), the peace version of the fallout routine, status codes 0, 1 and 5. The Offer Sheet's settlement logic (`TTradeMgr_SettleTrades`) is read, not tested.
- **Dialog identity**: a dialog's size gives its kind (production 276x149, construction 320x320) but not which building it belongs to (the text log can now tell: read the dialog's strings).
- **Technology Investment screen** (microscope button, where techs are bought): not looked at; hot key 5 shows only the history.
- Briefings through the registry survive a loaded save but not a new game; the Library and Load screens have no found way out except choosing.
- `names/names.tsv`: 0x4357b0 is now `TScreenBuilder_HelpAndSmallWindows` (likely: a switch on window id building the Help topics/tips window and other small windows; read from code, not seen in play). The 8 unnamed map-reading functions at 0x557e10-0x55a160 and 0x563990 moved from `ui_screens` to `military_ai` (they read `g_MapMgr` and sit among TPortZone/TOcean code; `names/groups.tsv`). `map_sim`, `display` and a few `nations_sim` placements near 0x5149d0 are still guesses.
- Slider quirk: clicking the slider track jumps proportionally and the right arrow adds one step; dragging the knob did not move it.

- **Mac/iPad**: `docs/mac_ipad.md` and `tools/mac/make_wrapper.sh` (private Wine wrapper on a Mac, then stream or emulate to the iPad). Written without a Mac: untested, fix as you go.

## Next steps (suggested order)

1. Done: University/Trade School, Transport, trade settlement, Shipyard, Armory, Indiaman. Left: the first-in-line rule and price formula (code notes in `docs/trade.md`; needs a Board of Trade
   with rival bids, so a fixture with more goods), and the full transport bar (unreachable with only food on the network: sliders stop at 'available', 10 of 15). Hussars $100 vs Skirmishers $200 not re-ordered.
2. Diplomacy leftovers above (order Empire where it is offered, ally with a Great Power, make a grant) if wanted.
3. Keep playing normally now and then with crash dumps armed (`dumps/`) to confirm the music fix.

## How to resume in a new session

1. Read `AGENTS.md`, this file, `docs/screens.md`, and the ends of `docs/production_playtest.md` and `docs/diplomacy.md`.
2. `git switch -c topic/<name>` (never commit on main), then `harness/prod_boot.ps1 -Fixture oil_plant_built -Restart` for a game to poke at.
3. Read screens with `prod_do.ps1 "mark; <action>; txt"` before taking a screenshot; end every game session with `harness/prod_end.ps1`.
