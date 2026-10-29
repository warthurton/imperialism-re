# Turn phase machine (TSimMgr_AdvancePhase, 0x57da70)

`TSimMgr` (280 bytes; vtable 0x662a58) drives a turn as a state machine. The current phase is stored at `+4`, the previous one
at `+8`. `TSimMgr_AdvancePhase` is one `switch` over that value; each case does its work, posts an event through
`g_Events` (vf19 = post message id) and writes the next phase. Phase handlers are TSimMgr vtable slots (slot 24 = trade).

Confidence: **confirmed** = decoded from code; **likely** / **guess** as in `names/names.tsv`. Edit this table as we learn.

| State | Next | What the code does | Meaning | Confidence |
|---|---|---|---|---|
| 1 | 3 | posts event 0x11f8 (or 0x5dc) | start / new-game entry | guess |
| 3 | 2 | save-state helpers (0x57c3b0 touches g_DiplomacyMgr and g_TradeMgr, 0x57c7c0 touches g_MapMgr, a "Chunk" string) | snapshot / autosave | guess |
| 2 | 0x10 or 0x13 | each great power vf3 and vf40; picks a human-vs-AI branch; calls slot 17 | per-nation setup | guess |
| 4 | 5 | posts event 0x7dd with the current turn | start of the turn proper | guess |
| 5 | 6 | loops while players/AI report not ready (0x502b60, 0x5df8d0) | wait for players | guess |
| 6 | 7 | `g_DiplomacyMgr.vf12`; shows messages | diplomacy phase | guess |
| **7** | 9 | **calls slot 24 = `TSimMgr_RunTradePhase`**; `g_DiplomacyMgr.vf13` | **trade phase** | likely |
| 9 | 10 | slots 17 and 22 | after trade | guess |
| 10 | 0x14 | `g_Game.vf23` | ? | guess |
| 0x14 | 0x15 / 0x13 | one call on an object at 0x6a3338 | ? | guess |
| 0x15 | 0xd / 0x13 | 0x57f0e0, `g_DiplomacyMgr.vf14`, 0x557040, 0x518130 (reads g_TradeMgr.vf20), 0x53fe30 (loops great powers) | likely end-of-turn bookkeeping (production/prices?) | guess |
| 0xd | 0x19 | 0x4a6dd0 | ? | guess |
| 0x19 | 8 | 0x581300, 0x581510 | ? | guess |
| 8 | 0xb / 0x13 | | ? | guess |
| 0xf | 0x12 | 0x55b8e0, 0x56da50 (builds text strings with g_Game), 0x54d4e0 | report / news text | guess |
| 0x11 | 0xf | 0x5af980, 0x5b0c20 | ? | guess |
| 0x12 | 5 | map manager vf19; posts event | back to waiting | guess |
| 0x64..0x72 | 4 | post an event each, then back to state 4 | one-shot events (messages) | guess |

Open question: where production actually runs (TCity_BeginTurn, order execution). Not found among the states above yet.

## Production (update)
* The nation's TCityInteriorMinister (class of the production screen) has a per-turn function `vf62` (guess: RunTurnOrders) that walks the 9 industry slots (index 0x19-0x21) and 8 other slots (0x2b-0x32); every slot with a pending amount calls `vf67` (guess: FundOrder).
* `vf67` takes the order object at nation+0xe4+slot*4 (the TItemOrder family), clamps the wanted amount, and removes the inputs and labor from stock. So orders are paid for at the end of the player's turn, not at "production".
* Still unknown: the caller of `TCity_BeginTurn` (virtual, slot 10) and the step that turns paid orders into goods. Next: look at TItemOrder vf+0x40 and vf+0x118 callees, and the TGreatPower per-turn methods.
* `TItemOrder_vf13` (likely, renamed `TItemOrder_Complete`) is the delivery step: amount goes into nation stock for the output good (nation+0x1fc), into a per-item total (nation+0xb6), and the order's input slots are cleared. `vf14` resets an order and re-applies the remembered amount.
* Not yet found: the loop that calls `Complete` for all orders at turn end (not in `TCityInteriorMinister_vf62`; probably in a TGreatPower method or a minister base class). Dead end noted: `FUN_005a9d90` is tactical-view UI drawing, unrelated.
