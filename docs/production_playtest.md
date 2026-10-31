# Production, checked against the running game (2026-10-29)

Method: `harness/prod_nav.ps1` launches the game to the map; clicks go through the real UI (`prod_click.ps1`, with
`focus.ps1` making sure the game has focus first); `tools/readcity.py` only *reads* the game's memory (the local human's
`TCity`, found as the one great power in `g_GreatPowers` at 0x6a4370 whose vtable is not `TAutoGreatPower`'s 0x654088) and
saves raw snapshots to `results/city_*.json` (kept in the repo as evidence: a few hundred bytes of city state each, no game code or assets). Nothing was written into the game's memory.

Setup: new game, Brosoptendall (power index 1), spring 1815. One order set in the Lumber Mill screen, then End Turn, trade
offers rejected, next turn.

| Check | Predicted by the code | Seen in the game |
|---|---|---|
| Starting capacity (max = left) for Textile, Clothing, Steel, Metal, Lumber, Furniture, Refinery | 2,1,2,1,2,1,0 (TCity_Reset) | 2,1,2,1,2,1,0 (also the Lumber Mill screen: "Capacity: 2", "Production 0 / 2") |
| Recipe cost shown | 2 labor + 2 Timber per Lumber **or** Paper | exactly that on screen; both sliders share one capacity |
| Labor | city labor object +0x1c | 16 = the number beside the labor icon on the capital screen |
| Set Lumber to 1 | Timber -2, labor -2, LumberMill capacity left -1, order amount 1, 2 Timber reserved | Timber 40 -> 38, labor 16 -> 14, capacity left 2 -> 1, amount 1, reserved Timber 2, remembered (+0x4c) 1 |
| Next turn start | Lumber +1 (Complete), score = old*0.9 + total*10 | Lumber 20 -> 21, order total (+0x44) 0 -> 1, score 0 -> 10 |
| Turn counter | +1 in TCity_BeginTurn | city+0xc 0 -> 1 |
| Military upkeep | not modelled | -$150 per turn at start (cash 50,000 -> 49,850) |

## What the test taught us (and the model got wrong)

1. **Orders persist.** After delivery the same order is charged again from the new stock: amount still 1, 2 more Timber
   taken (38 -> 36), capacity left 2 -> 1 again. This is `TItemOrder_ResetAmount` re-applying the remembered amount (+0x4c).
   My first model zeroed orders each turn; `reimpl/production.c` now repeats them (and keeps the remembered figure if
   inputs run short).
2. **Labor is refilled each turn** (stayed 14 = 16 refilled, minus 2 for the re-charged order), rather than staying spent.
3. **Raw goods arrive on their own.** At turn start Cotton, and two stock slots beyond the 17 goods, rose by 1 with no
   order and no trade (arrivals from the starting territory; the arrivals array was already empty when read).
4. The stock array has 6 slots after the 17 goods: 10, 5, 0, 5, 0, 0 at the start; meaning not decoded yet.

## Not covered
Multi-input recipes (Steel, Fabric) and the capacity-limit/labor-limit "binding" codes were not exercised in play; Food,
training, power plant and unit orders were not exercised either. The turn phase seen was one full season.

## Second run: Steel and Fabric (multi-input recipes)

Steel Mill (the waterwheel building by the river) and Textile Mill (the farmhouse in the middle of the capital screen).
Start state: Cotton 20, Wool 20, Coal 30, Iron 30, Steel 20, Fabric 20, labor 16.

| Check | Predicted | Seen |
|---|---|---|
| Steel to 1 | Coal -1, Iron -1, labor -2, SteelMill capacity -1 | Coal 30->29, Iron 30->29, labor 16->14, capacity 2->1, order reserved {Coal 1, Iron 1} |
| Steel to 2 | one more of each | Coal 28, Iron 28, labor 12, capacity 0 |
| Steel to 3 | refused: capacity is 2 | slider stops at 2, nothing changes |
| Steel back down to 1 | everything refunded | Coal 29, Iron 29, labor 14, capacity 1 |
| Fabric to 1 | 1 Cotton + 1 Wool, labor -2, capacity -1 | Cotton 19, Wool 19, labor 12, capacity 1 (reserved {Cotton 1, Wool 1}) |
| Fabric to 2 | again | Cotton 18, Wool 18, labor 10, capacity 0 |
| Next turn start | Steel +1, Fabric +2, score = (1+2)*10 = 30, orders re-charged | Steel 20->21, Fabric 20->22, score 30; Cotton/Wool 18->16, Coal/Iron 29->28; labor 10 = 16 - 2 - 4 |

Findings:
* The Textile Mill screen draws "2 Cotton -or- 2 Wool", but the game takes **1 Cotton + 1 Wool per unit** (the preferred even
  split in `TOrItemOrder_vf11`). The "or" only matters when one of them runs short; that branch was not exercised.
* Steel needs both inputs in equal amounts, so the scarcer one limits it; capacity and labor limit it the same way as Lumber.
* Raw arrivals vary per turn: this time Grain +2, Fish +3, Meat -1 (slots 17-20 are Grain, Fruit, Fish, Meat; confirmed
  by the Warehouse screen: Fruit 5, Grain 10, Fish 0, Meat 5 at the start). Cotton/Wool got no arrival this turn.
* Other screens seen while looking for the Textile Mill (all in the capital): Lumber Mill, Steel Mill, Clothing Factory
  (2 labor + 2 Fabric), Furniture Factory (2 labor + 2 Lumber), Metalworks (2 labor + 2 Steel -> Hardware or Arms, one shared
  capacity), Food Processing (2 labor + 2 Grain + 1 Fruit + Fish or Meat -> 2 Food), Trade School (1 Paper + $100, then
  2 Paper + $1,000, confirming the training costs), Armory (a unit costs trained labor + 1 Arms + $200), University, Shipyard
  (a Trader costs 2 Fabric + 4 Lumber), Warehouse, Railyard.

## Third run: shortage branches (stock set up with `tools/poke_stock.py`, orders always set through the real UI)

The fixture only writes goods stock or labor into memory to create the shortage; the game's own `SetAmount` / `Complete` code does
everything else. Binding code = order+0x40 (0 inputs, 1 labor, 2 capacity).

| Case | Predicted | Seen |
|---|---|---|
| Fabric with Wool 1, Cotton 10: unit 1 | 1 Cotton + 1 Wool | Cotton 10->9, reserved {Cotton 1, Wool 1} |
| ...unit 2 (no Wool left) | Cotton covers both: 2 Cotton | Cotton 7, reserved {Cotton 3, Wool 1}, amount 2 |
| ...lower back to 1 | refund evenly | Cotton 8, Wool 1 given back; the order now holds {Cotton 2} (so the refund is taken from what the order holds, first input first) |
| Steel with Coal 1, Iron 10: unit 1 then a second click | 2nd refused, binding 0 | stays at 1, binding 0; the dialog shows a red x under Coal |
| Lumber with Timber 3: 1 unit then a second | refused (2 Timber left of 3 is 1 < 2) | Timber 1, stays at 1, binding 0 |
| Paper with labor 3: unit 1 then a second | refused, binding 1 (labor) | labor 3->1, stays at 1, binding 1 |
| Next turn with Wool, Cotton and Coal at 0 | Fabric and Steel orders cannot be re-charged: amount 0, remembered kept | Fabric amount 0 / remembered 2, Steel amount 0 / remembered 1; capacity back to 2 for both; the Interior Minister warned "idle workers" |
| The turn after, with Wool, Cotton and Coal at 1 | orders come back as far as stock allows | Fabric amount 1 (remembered 2), Steel amount 1 (remembered 1); Paper/Lumber orders unaffected |

So the model is right on every branch tested: costs, the either/or fill-in, refunds, the three limits and their codes, and remembered
amounts that survive a shortage and are re-applied when stock returns (`order_reset_amount` in `reimpl/production.c`).

## Things learned about the game and the test setup

* **Hot keys work in the real game** (readme section XI): `1`..`5` open the transport/industry/trade/diplomacy/technology screens,
  `Esc` returns to the map, `Esc` rejects a trade offer sheet (10 offers rejected with 10 key presses), `Return` accepts one.
  `Return` does not press OK on a confirmation dialog, and `Esc` did not dismiss the diplomacy alliance offer.
* **Preferences** are stored in the registry (`HKCU\Software\SSI\Imperialism\Settings`): `Pref2` effects volume (0-100),
  `Pref3` music volume (0-255), `Pref8` minister warnings, `Pref10` minister briefings. A new game switches briefings back on, so
  `harness/prod_prefs.ps1` turns them off again through the Preferences screen.
* **Music silently disappears** when Windows' compatibility assistant adds `IgnoreFreeLibrary` to the exe's compatibility layers
  (it did after a crash): the loader then takes the system `winmm.dll` instead of the player in the game folder. Removing that flag
  (keep `HIGHDPIAWARE`) brought the music back; `prod_nav.ps1` now removes it and `prod_music.ps1` checks the audio meter.
* **Saves** can be loaded back (`harness/prod_load.ps1`); `saves/` holds named fixtures.

## Fourth run: the non-recipe orders (training, Food, Metalworks, Armory, Railyard, Capitol)

Same method (real UI; memory only read, except the stock fixtures noted). Costs are charged the moment the slider moves.

| Order (screen) | Cost per step, as charged | Delivered | Seen |
|---|---|---|---|
| Trade School: untrained -> trained (slot 23) | 1 labor, 1 Paper, $100 | next turn start | Paper 20->19, cash 50,000->49,900, labor 16->15 |
| Trade School: trained -> expert (slot 24) | 2 labor, 2 Paper, $1,000 | next turn start | Paper 19->17, cash 49,900->48,900, labor 15->13 |
| Food Processing (slot 7), 1 step = 2 Food | 2 labor, 2 Grain, 1 Fruit, 1 Fish **or** Meat | next turn start, +2 Food per step | two steps: labor -4, Grain 10->6, Fruit 5->3, Meat 5->3; next turn Food 20->24 |
| Metalworks: Hardware (slot 15) | 2 labor, 2 Steel | next turn, +1 Hardware (counts in the production score) | Steel -2, labor -2; Arms refused afterwards because the one capacity was used (binding code 2) |
| Armory: Skirmishers (units, slot 25+) | 1 worker, 1 Arms, $200 | next turn start: newspaper popup "1 regiment of Skirmishers reporting for duty" | Arms 10->9, cash -200, total workers 7->6 (an untrained one) |
| Railyard: rail car (slot 51) | 2 labor, 1 Lumber, 1 Steel | next turn (adds transport capacity, not a stock good) | reserved {Lumber 2, Steel 2} for 2 cars; no stock change at delivery |
| Capitol: population growth (slot 60), capacity 2 | 1 Food, 1 Clothing, 1 Furniture, **no labor** | next turn: one more worker | Food/Clothing/Furniture 5->4 each; total workers 6->7 after the turn |

Observations:
* **Orders from different screens persist differently.** Recipe orders (items 8-16) remember their amount and are re-charged
  every turn. Training, Food, unit, Railyard and Capitol orders did not come back after delivery (amount 0, remembered 0 or
  stale); only a recipe order such as Hardware repeated (amount 1, Steel -2 again, score 19 = 10 x 0.9 + 1 x 10).
* **The production score counts only recipe orders**: Food +4 and the training/unit deliveries did not change it.
* The three worker grades after two promotions and one unit: untrained 2 -> 0, trained 3 -> 3, expert 2 -> 3 (left-hand column on
  the capital screen), consistent with each order consuming one worker of its input grade.
* **Power plant**: no screen in the capital offered a power-plant order, so `TPowerPlantOrder` stays untested (it may only
  appear later in the game or through a technology).
* **Stacked dialogs**: the dialogs' close buttons sometimes ignore a click; the back arrow (top-left) always leaves the screen.

## Food Processing shortage (fixture: Fish and Meat set through memory, order through the real UI)

| Case | Seen |
|---|---|
| Fish 0, Meat 0, Grain 10, Fruit 5, labor 16: one step | refused; the screen draws a red x under the Fish/Meat icon; nothing charged |
| Meat 1: one step | accepted: Meat 1->0, Grain 10->8, Fruit 5->4, labor 16->14, order amount 2 Food |
| Fish 0, Meat 0 again: a second step | refused (stays at 2) |
| Fish 1: a second step | accepted: Fish 1->0, Grain 8->6, Fruit 4->3, labor 14->12, order amount 4 Food |

So the Fish-or-Meat input is one unit of either, taken from whichever is available. The power plant remains untested: it needs the
oil-drilling technology (not available at the start of a game; the game text says it also enables Refinery and Power Plant).

## Power plant (2026-10-30): built and run through the real UI

**What gates it.** The capital screen (`TCityProductionView`, vf53 hot text and vf71 click handler) treats building types 6 (Oil
Refinery) and 0xb (Power Plant) specially: the site is only live when `TTechMgr` per-power record `+0x268 + power*29 + 19` equals
**2** ("owned"), where `power` is `g_Game+0x2e` (the local human). **That index changes between new games** (0 in one, 6 in the next), so a poke aimed at a fixed power silently misses; `poke_tech.py L:19` looks it up. The global known-tech byte `+0x193`
is a different thing (it only unhides Oil in the warehouse, prospector and trade screens). A new game starts with techs 0-2 at 2 in
every power's record. The sites are invisible hotspots: `harness/prod_hover.ps1` (hover grid, records the hot text) showed 14
building names before and 16 after, the new ones being "Site for Factory: Oil Refinery" (930,420) and "...: Power Plant" (1080,470).
`tools/poke_tech.py L:19` sets the record (fixture; the real route is buying Oil Drilling at the University/Trade School).

| Step (real UI) | Seen | Notes |
|---|---|---|
| Click the Power Plant site | constructor dialog: "Power Plant, Cost to Build $5,000", text "converts one unit of fuel into six units of power", "up to 100 units of fuel per turn" | matches game strings 8597/8598 |
| OK | cash 50,000 -> 45,000 at once; scaffolding on the site; labor, stock unchanged | `TBuildingConstructionView` |
| Next turn start | plant finished (building drawn); dialog "Power Plant, Production: 0" with a 0 slider | upkeep -$150 as usual |
| Slider +1 (Fuel set to 20 beforehand with `poke_stock.py`) | **Fuel 20 -> 19, labor 16 -> 22**, labor+0x1e (power) = 6, a bulb "6" appears beside the labor icon | 1 fuel = 6 power, as predicted (`TPowerPlantOrder_vf16`: amount x 6) |
| Next turn start, nothing touched | **Fuel 19 -> 18**, labor stays 22 (16 refilled + 6 power) | the order repeats like the others; the manual's "power is created the same turn it is used" holds |

Not tested: the 100-fuel cap, shortage (Fuel 0), and the Refinery (not needed here).

**Harness.** `prod_vol.ps1 -Mode test` now means effects 10% and music about 5% and also sets minister warnings and briefings Off in the
registry before launch (a new game still resets briefings to On; a loaded save keeps them). `prod_nav.ps1` no longer starts the
idle-dock watcher (it shrank the window after 10 s and broke hover scans). `shot.ps1` takes a focused screenshot.

**Faster harness.** `harness/prod_do.ps1 "city; m 1000 400; w 0.3; plant; s shot1"` runs a chain of clicks in one process. `fast.ps1`
replaces the fixed sleep after each click with "wait for the screen to start changing, then to settle" (a plain settle check
returned before slow screen transitions had begun, so it first waits for a change). Map to construction dialog went from about 15 s
of separate scripts to about 7 s. After entering a screen, move the mouse once before clicking a hotspot.

## Oil Refinery (2026-10-30): built and run through the real UI

Same gate as the Power Plant (the local power's tech-19 record = 2; see above), and again set up with `tools/poke_tech.py L:19` plus
Oil 20 from `poke_stock.py`. The local power's index was 5 in this game (0 and 6 in the earlier ones), which is why the tool looks it up.

| Step (real UI) | Seen | Notes |
|---|---|---|
| Click the "Site for Factory: Oil Refinery" (930,420) | dialog "Oil Refinery, Capacity: 2", cost shown as 2 Lumber + 2 Steel, text "two units of labor plus two units of oil to produce one unit of fuel" | manual: one Lumber and one Steel per point of capacity; a mill starts at capacity 2 |
| OK | Lumber 20 -> 18, Steel 20 -> 18 at once; cash unchanged (50,000); capacity still 0 | scaffolding on the site |
| Click the same site again while it is pending | dialog with Cancel; **Cancel refunds**: Lumber and Steel back to 20 | matches the game's "Cancel construction." strings 8099 |
| Build again, end the turn | at the next turn start `cap_max` and `cap_left` for the Refinery = **2** (cash -150 upkeep only) | |
| Production dialog: slider +1 | Oil 20 -> 18, labor 16 -> 14, `cap_left` 2 -> 1, order amount 1 | per unit 2 Oil + 2 labor + 1 capacity |
| slider +1 again, then a third click | Oil 16, labor 12, `cap_left` 0, amount 2; the third click is **refused** (binding code 2 = capacity) | |
| End turn | next turn start: **Fuel +2**, order repeats (Oil 16 -> 12, labor refilled 16 then -4 = 12, `cap_left` 0 again), production score 20 = 2 x 10 | same repeat rule as every other recipe |

Not tested: expanding the Refinery with the button in its dialog, cancelling the Power Plant (probably refunds the $5,000), and
building the sites on Normal/Hard settings (this game started with the six industries already built).

`reimpl/production.c` now models both buildings (`build_refinery`, `cancel_refinery`, `build_power_plant`, `power_set_fuel`, and
the turn-start completion / re-application in `city_begin_turn`); its self-test asserts the numbers in these two tables.

## Reading the screen from memory

`tools/readview.py` dumps the game's `TViewMgr` (global 0x6a21bc, 0xfc bytes). Diffing the dump on the capital screen and the terrain
map showed that the **low half of the dword at +0x04 is the current screen id**: 0x7db (2011) = capital, 0x7dd (2013) = terrain map; a
pointer at +0xf0 is set only on the map. `readview.py id` prints just that number. Dialogs (constructor, production sliders) are child
windows and do not change this object, so a dialog still has to be told from a screenshot or found in another object (open question).
It already paid for itself: a `back` click that a dialog swallowed was caught because the id stayed 2011, which a screenshot-settle
check would have missed. `readcity.py` (stock, capacity, labor, cash) remains the way to read the economy.

## Telling which dialog is open (answer to the open question above)

Not from the game's own objects (I did not find one that tracks dialogs), but from Windows: every dialog is an `AmbitMcWindow` child of
the game frame, so `harness/prod_wins.ps1 -Visible` (or `Get-Dialog` in `fast.ps1`) lists it with its rectangle, no screenshot needed.
On the map there is none; in the capital with a dialog open there is exactly one. Sizes seen (game pixels): **320x320 = construction
dialog**, **276x149 = production dialog** (Steel Mill, Capitol and Refinery all the same, so the size gives the kind, not the building).
The position changes with the site it opens from (Capitol at (60,210), Steel Mill at (203,72), constructors at (147,64)), so fixed click
coordinates for sliders only ever worked for one site. The dialog's rect fixes that: controls sit at a constant offset inside it
(production: X at (262,12), slider right arrow (241,123), left arrow (77,122); construction: OK (273,301), Cancel (39,301)), and the
mirror shows the 640x480 game area at 1.993x starting at (10.4, 34.5) in mirror units. `prod_do.ps1` now has `dlg`, `dwait`, `dplus N`,
`dminus N`, `dclose`, `dok`, `dcancel`; site clicks wait for their dialog, and `back` closes any open dialog first. Checked on the Steel
Mill: `dplus 2; dminus 1` left the order at 1 (capacity left 2 -> 1, labor 16 -> 14) and `dminus 1` returned it to 0.

## Refinery expansion and the two cancel paths (2026-10-30), run from a saved game

These ran from the fixture `saves/oil_t0.imp` (below), not a fresh game plus pokes.

| Step (real UI) | Seen | Notes |
|---|---|---|
| Refinery dialog, factory-arrow button (top right) | overlay "Expand Factory": "Oil Refinery, Capacity: 4", cost 2 Steel + 2 Lumber, Cancel / OK | the overlay is not a separate `AmbitMcWindow` |
| OK | Lumber 18 -> 16, Steel 18 -> 16, cash unchanged, capacity still 2; a hammer icon appears in the production dialog, hot text "Expansion in Progress" | the hammer is only a marker, clicking it does nothing |
| Press the expand button again | the same "Capacity: 4" dialog is offered again | |
| Cancel in that dialog | **expansion cancelled and refunded**: Lumber 18, Steel 18; capacity stays 2 after the turn | so Cancel here means "cancel the pending expansion" |
| Expand again, OK, end turn | at the next turn start `cap_max` = `cap_left` = **4** | cost is 1 Lumber + 1 Steel per point, same as building |
| Power Plant under construction: click the site, Cancel | cash $45,000 -> $50,000 (**$5,000 refunded**); header says "Power Plant Under Construction" while pending | matches the Refinery's cancel |

`reimpl/production.c` gained `expand_refinery`, `cancel_refinery_expansion` and `cancel_power_plant`, with checks for all of the above.

**Saved games as fixtures.** A save keeps the tech records and the stock: after loading `oil_t0` the local power's tech-19 record
still read 2 and Oil/Fuel were 20/20, so no poking is needed. Loading also fixes the world and the local power index (2 in these
saves), which a fresh game randomises. The title screen has no load option (its book opens the scenario and tutorial list), so a fixture
still needs a launch and a new game first (`prod_nav.ps1`, about 35 s) and then `prod_load.ps1 <name>` (about 20 s); the saving is in
skipping setup, not in the launch. Use a fixture whenever a test needs the oil-age state or a mid-game situation.

## Power Plant limits (resolved, 2026-10-31)

* **No cap at 100 fuel.** The order's amount is counted in *power* units (6 per fuel) and its maximum is the amount already set plus the Fuel in stock x 6
  (`TPowerPlantOrder_vf12`); `SetAmount` only checks 0 <= new <= maximum. With 150 Fuel the slider reached 150 fuel = **900 power** (stock 0, labor 16 -> 916). The help
  text's "up to 100 units of fuel per turn" is not enforced anywhere in the code. (My earlier 141 / 142 were only where a click landed on the slider track.)
* **Clicking the slider track jumps to that point proportionally; the right arrow adds one fuel (6 power).** Dragging the knob did not move it.
* **Running out of Fuel**: the standing order (900) survives. At the next turn start with 0 Fuel the plant gave 0 power (labor back to 16); after giving the city 30 Fuel the turn
  start gave **180 power** (30 fuel, all burned) with the 900 still remembered: the order is re-applied up to what is available (`TPowerPlantOrder_vf14`: if the maximum is below the
  remembered amount it sets the maximum, then tries the remembered amount, which is refused).
* Fixture `oil_plant_built` (turn 4, Power Plant built, Refinery capacity 4) is the starting point for these tests.
