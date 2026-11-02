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

## Orders (TCivUnit_vf13 = SetOrder(order, target), 0x5c29f0; TCivUnit_vf11 = End Turn tick, 0x5c2a90; completion = FUN_004d4390)

SetOrder stores the code at +8, the target at +0xc and the duration from this table (indexed by code): `0:0 1:0 2:0 3:0 4:0 5:1 6:3 7:3 8:1 9:0 10:3 11:3 12:4 13:1` turns.
The tick: orders **5-8 and 10-13** count `+0x24` down and, at 0, finish through `FUN_004d4390` (switch on `code - 5`) and reset the state to 0; **2 (sleep) persists**; any other code resets to 0 at once.

| Code | Meaning | Evidence |
|---|---|---|
| 0 | idle | confirmed |
| 1 | **a move or search ordered to a tile**: the unit's tile (+6) changes at once, +0xc keeps the tile it came from (what Rescind restores). A Prospector's "search this tile" reads 1 (seen) | confirmed in play |
| 2 | **Sleep** (button (621,166)); persists | confirmed (0 -> 2 on the button) |
| 3 | redeploy ("Redeploying" in the report) | likely |
| 4 | **No orders this turn** (button (592,166)); reset by the tick | confirmed (0 -> 4) |
| 5 | **Engineer lays rail**: completion calls MapMgr slot 0x68 = `0x513f60` (adds both rail bits), sets +0x26 = 9001; 1 turn, $100 at once | confirmed (rail order seen, code) |
| 6 | **Depot**: completion calls MapMgr slot 0x124 = `0x5145b0` (sets tile flag 0x10, charges $2,000 at order time), 3 turns | confirmed by code and by the 3-turn depot in play |
| 7 | **Port**: slot 0x128 = `0x5147d0` (sets flag 0x04, $3,000), 3 turns | code-confirmed, not ordered in this check (the earlier ports in play took the same time) |
| 8 | **Prospect**: completion does `tile+0x0d \|= 1 << nation` (the prospected mask) and, for the AI, may report a find (+0x26 = 9007); 1 turn. The AI path (`production.c`) sets it for Prospectors (type 1). A human's order reads 1 first (see above) | code-confirmed |
| 10 | **Improve a tile one level** (Miner type 0 or type-8 units use resource slot 1, others slot 0: `MapMgr +0xc8` reads the level, `+0xcc` writes level+1); 3 turns. The AI calls it for farm/mine tiles | code-confirmed; which unit types: not tested |
| 11 | 3-turn job with **no case in the completion switch** (so nothing is applied there; probably handled elsewhere, e.g. Rancher/Forester work) | open |
| 12 | **Fort**: slot 0x12c = `0x5149d0`, 4 turns, applies to the province (+ province record) | code-confirmed (matches "forts are built throughout the province") |
| 13 | **Developer buys land**: sets tile `+0x18` = nation (land bought in a minor); 1 turn | code-confirmed (the AI calls it for type 7) |
| 9 | no work, duration 0 | unused |

Unit types seen in the AI order code: 0 Miner, 1 Prospector, 2 Farmer, 4 Engineer, 7 **Developer**; 3, 5, 6, 8 are the remaining civilians (Rancher, Forester, Driller, and one more: untested).

* "Time to completion: N months" in the Civilian Report is `(+0x24 - 1) * 3` (rail 0 months, depot 3 months after its first End Turn).
* Selecting a unit with Next Unit clears a sleeping/no-orders state (+8 back to 0, +0xc to -1) in the cases seen.
* Units given work are not in the cycle; the cycle (Next Unit) walks the list in order and skips units that are asleep, skipped, or working.
* **Correction recorded here**: the prospected flag is tile `+0x0d` (bit = nation), not `+0x01` (`docs/map.md`).
* Tool: `tools/vtable_slots.py <vtable> <offsets...>` reads exe vtable slots and follows the `jmp` thunks (used for MapMgr 0x6587e0).

## Open

* Code 11, and which unit types use 3, 5, 6, 8 and exactly which tile kinds each improvement code applies to (order one Farmer and one Miner improvement and read +8).
* Developed levels: stored by MapMgr slot 0xcc (not yet located on the tile).
* The autoplayer's "needs orders" test: a unit is in the Next Unit cycle when +8 is 0 (FUN_005c2980 also lets 3 through), so `readunits.py` + `+0x08 == 0` replaces pixel guesses.
