# Status: where the project stands

Update this file at every ship (and before ending a session). It is the first thing to read after `AGENTS.md`.
Last updated: 2026-10-31 (diplomacy decoded in part).

## Done and verified (in the running game unless noted)

- **Display shim** (`shim/`): windowed scaling, maximize, fullscreen with integer scale, mouse mapping; music crash investigated, `winmm/` rebuilt
  from a maintained ogg-winmm. The music-loss crash is intermittent and **not proven fixed**.
- **Decompile**: 10.9k functions named; `src/` groups (git-ignored) from `tools/split_source.py`, no function left unsorted (the last-resort
  `late`/`laddr` rows are filing guesses, audited with `tools/audit_groups.py`). The Board of Trade screen builder (0x4601b0) decompiled with `ghidra/Probe.java`.
- **Turn flow**: `TSimMgr_RunLocalPowers` (phase 8) runs `CompleteOrders` for every locally simulated power, the human included; `BeginTurn` is
  phase 0x12 (`docs/turn_phases.md`, `docs/how_a_turn_works.md`).
- **Production** (`docs/production_playtest.md`, model in `reimpl/production.c`, self-tested): all recipes, shortage cases, training, units, Food,
  capacity, **Power Plant** (build $5,000, 1 Fuel = 6 power, repeats, cancel refunds), **Refinery** (build 2 Lumber + 2 Steel, expand +2 for 2 + 2,
  cancel and expansion-cancel refund). Oil-age sites are live only when the local power's tech-19 record is 2.
- **Test harness** (`harness/`): `prod_boot.ps1` loads a save from the title screen in about 11 s; `prod_do.ps1` chains clicks, hot-key screen
  changes (`go ...`), dialog steps from the dialog's real window rect; `prod_endturn.ps1` finishes a turn in about 7 s by screen id.
  State is read from memory (`tools/readcity.py`, `readview.py id`, `readtech.py`, `readprefs.py`). Screens, ids and the main menu: `docs/screens.md`.
- **Diplomacy** (`docs/diplomacy.md`): manager data layout, setters, status codes seen in play, an overture experiment; tested model `reimpl/diplomacy.c`.
- **Fixtures** (`saves/README.md`): `oil_t0` (oil age ready), `oil_refinery4`, and the earlier production ones.

## Open questions

- **Power Plant limit**: the slider took 141 and 142 fuel from a stock of 150, so the game text's "100 fuel per turn" is not what it enforces; the real
  limit is unknown. What happens at the next turn start when a standing order outruns the Fuel stock is untried. `reimpl/production.c` still carries
  the 100 cap (unconfirmed).
- **Dialog identity**: a dialog's size gives its kind (production 276x149, construction 320x320) but not which building it belongs to.
- **Technology Investment screen** (the microscope button, where techs are bought): not looked at; the hot key 5 shows only the history.
- **Briefings through the registry** survive a loaded save but not a new game; the Library and Load screens have no found way out except choosing.
- `names/names.tsv`: 0x4357b0 is another screen builder with no identifying strings yet.
- `map_sim`, `display` and a few `nations_sim` placements near 0x5149d0 are guesses.

## Next steps (in this order)

1. **Diplomacy, continued** (`docs/diplomacy.md`, model `reimpl/diplomacy.c`, tool `tools/readdiplo.py`): the manager's data and its setters are decoded
   and seen in play (status 4 = peace, 6 = war; scores; war fallout -50/-40/-9). Still open: where overtures are queued and applied at End Turn, where consulates
   and embassies live, the war ripple, Pact/Empire/Peace acceptance. Next try: follow `TForeignMinister*` and the Great Power's virtual slots around 0x2a8 and
   0x290, and watch memory around the Minor Nation objects while ordering a consulate.
2. Power Plant limit and the out-of-fuel turn (fixture `oil_refinery4`, `poke_stock.py Fuel=...`).
3. The next least-verified systems: training (University, Trade School), transport, trade settlement (`TTradeMgr_*` read in the code, never checked in play).
4. Keep playing normally now and then with crash dumps armed (`dumps/`) to confirm the music fix.

## How to resume in a new session

1. Read `AGENTS.md`, this file, `docs/screens.md`, the end of `docs/production_playtest.md`.
2. `git switch -c topic/<name>` (never commit on main), then `harness/prod_boot.ps1 -Fixture oil_refinery4 -Restart` for a game to poke at.
3. End every game session with `harness/prod_end.ps1`.
