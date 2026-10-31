# Transport screen (hot key 1, screen id 2014)

Seen in the real game (fixture `oil_plant_built`, read with the text log), not just read in code. Model: `reimpl/transport.c`, self-tested.

* The screen is a book: **Transport** page (left) with one slider per commodity that exists on the network (greyed icons = not available yet), **Ledger** page (right) with the
  greyed-out industrial goods and, at the bottom, the capacity bar. Text read: slider labels `1 / 1`, `4 / 4`, `5 / 5` (moved / available) and the bar `10 / 15` (used / capacity).
* At the start only the food rows are live: Fish+Meat (shared slider), Fruit, Grain. The bar's used figure is the **sum of the sliders**.
* An arrow click moves a slider one step (grain 5 -> 4 -> 3, bar 10 -> 9 -> 8). The setting is **remembered** across turns (still 3/5 after End Turn).
* What is moved arrives for the next turn: stock before/after one End Turn, 5 workers:

| Turn | Sliders (fish+meat / fruit / grain) | Stock before (grain, fruit, fish, meat) | after |
|---|---|---|---|
| 5 -> 6 | 1 / 4 / 3 | 16, 16, 2, 3 | 16, 19, 2, 3 |
| 6 -> 7 | 1 / 4 / 5 | 16, 19, 2, 3 | 18, 22, 2, 3 |

  That is: stock changes by moved minus eaten, and the five workers ate **3 Grain, 1 Fruit, 1 Fish-or-Meat** (the right-hand food bar on the Industry screen read 4 / 2 / 1 for the
  seven workers before the two experts left as civilians, 3 / 1 / 1 afterwards). The split rule itself is not derived (code: `TPopulationMgr`, not read yet).
* Capacity: 15 at the start of the fixture (a Railyard rail car adds to it, see `production_playtest.md`). Not testable in this fixture: the bar being full. A slider never goes above its "available" figure (1 + 4 + 5 = 10 here), so with only the food rows live the bar cannot pass 10 of 15; it needs more goods on the network (Miners/Farmers connected by an Engineer, or more Railyard capacity cut down). Greyed rows show no demand lines, and the bar is red up to the used part. Also not tested:
  the demand lines (red/green under a slider), and the industrial rows (they need Miners/Farmers connected by an Engineer).
* Harness: `prod_do.ps1 "go transport; mark; c 328 421; txt"` (left arrow of the Grain slider at (328,421) mirror units, right arrow (578,421); fruit row y 359, fish+meat y 297).
