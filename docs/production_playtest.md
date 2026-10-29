# Production, checked against the running game (2026-10-29)

Method: `harness/prod_nav.ps1` launches the game to the map; clicks go through the real UI (`prod_click.ps1`, with
`focus.ps1` making sure the game has focus first); `tools/readcity.py` only *reads* the game's memory (the local human's
`TCity`, found as the one great power in `g_GreatPowers` at 0x6a4370 whose vtable is not `TAutoGreatPower`'s 0x654088) and
saves raw snapshots to `results/` (git-ignored). Nothing was written into the game's memory.

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
