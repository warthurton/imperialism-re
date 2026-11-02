# Civilian units in memory (decoded 2026-11-01, in progress)

`tools/readunits.py` reads them (read-only). A civilian is a **TCivUnit**: 40 bytes (0x28), a 36-byte `TUnit` plus 4, vtable 0x66ee60 (class descriptor 0x66ed58, constructor `TCivUnit_Create` 0x5c2860).

* **Where**: every Great Power keeps its civilians in an MFC pointer list at **nation +0x89c** (the structures list is at +0x898): `{vtable, ?, head, tail, count, ...}`, nodes `{next, prev, data}`. Each unit is also on its tile: tile `+0x20` points at the first unit there and units on one tile chain through unit `+0x14` (`+0x10` = previous).
* **The selected unit** is `*( *0x6a43dc + 4 )`: global 0x6a43dc points at a small object whose `+4` is the unit pointer. Found by scanning the whole process for pointers to my units, pressing Next Unit, and scanning again (`tools/scan_heap.py`); the on-screen panel name matched each time.

| Offset | Meaning | Status |
|---|---|---|
| +0x04 short | **type**: 0 Miner, 1 Prospector, 2 Farmer, 4 Engineer (3, 5, 6 are probably Rancher, Forester, Driller: not yet seen) | confirmed for 0, 1, 2, 4 (panel name vs type while cycling; 0 by elimination: the Miner I put to sleep) |
| +0x06 short | current **tile index** (y*108+x); -1 = none. Changes **immediately** when a move or build order is given | confirmed |
| +0x08 dword | **order code** (see below); 0 = idle | confirmed (constructor, SetOrder, tick) |
| +0x0c short | **order target / origin tile**: set by SetOrder; -1 while idle. After a rail order it held the tile the Engineer came from (what "Rescind" restores) | confirmed on one rail order; semantics for other orders open |
| +0x10, +0x14 | previous / next unit on the same tile | confirmed (`TCivUnit_vf10`) |
| +0x18 dword | owning nation | confirmed |
| +0x20 dword | unit id (original units 360-364 for my power, later ones 1015, 1016) | confirmed pattern |
| +0x24 short | **turns of work left**; set by SetOrder from a table, decremented each End Turn | confirmed |
| +0x26 short | -1 | unknown |

## Orders (TCivUnit_vf13 = SetOrder(order, target), 0x5c29f0; TCivUnit_vf11 = End Turn tick, 0x5c2a90)

SetOrder stores the code at +8, the target at +0xc and the duration from this table (indexed by code): `0:0 1:0 2:0 3:0 4:0 5:1 6:3 7:3 8:1 9:0 10:3 11:3 12:4 13:1` turns.
The tick: orders **5-8 and 10-13** count `+0x24` down and, at 0, finish (`FUN_004d4390`: apply the work) and reset the state to 0; **2 (sleep) persists**; any other code resets to 0 at once.
`FUN_005c2980`: the unit still takes orders (is in the Next Unit cycle) when the code is 0, 2 or 3... but see the observation below.

| Code | Meaning | Status |
|---|---|---|
| 0 | idle | confirmed |
| 2 | **Sleep** (button at game (621,166)); stays until woken | confirmed (button press changed 0 -> 2) |
| 3 | probably **redeploy** (a move: "Redeploying" in the report, duration 0, target in +0xc) | likely (the report text; code seen on a unit that had deployed) |
| 4 | **No orders this turn** (button at (592,166)); skipped by Next Unit, reset by the tick | confirmed (button press 0 -> 4) |
| 5 | **Engineer lays rail** (1 turn, $100 charged when ordered) | confirmed |
| 6, 7 | 3-turn jobs: the Engineer's **Depot** (3 turns seen) and probably **Port** | likely, which is which untested |
| 8 | 1-turn job: probably a **Prospector search** | guess |
| 10, 11, 12, 13 | 3, 3, 4, 1 turn jobs: the Miner/Farmer/Rancher/Forester/Driller improvements and Fort | guess |

* "Time to completion: N months" in the Civilian Report is `(+0x24 - 1) * 3` (rail 0 months, depot 3 months after its first End Turn): consistent with the depot taking three End Turns.
* Selecting a unit with Next Unit clears a sleeping/no-orders state (+8 back to 0, +0xc to -1) in the cases seen.
* Units given work are not in the cycle; the cycle (Next Unit) walks the list in order and skips units that are asleep, skipped, or working.

## Open

* Which code is Depot, Port, Fort, Prospect, Mine, Farm, Ranch, Forest, Drill: find the callers of SetOrder with literals (many take 0/1/2/4 only; the build orders come from the construction popup and the unit toolbar), or order each once and read `+8`.
* What `FUN_004d4390` does at completion (rail, depot, port, prospect, development level) and where developed levels are stored.
* The cycle order and the "needs orders" test for the autoplayer, to replace pixel guesses by `readunits.py sel`.
