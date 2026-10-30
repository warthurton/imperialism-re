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
