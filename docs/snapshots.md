# State snapshots

`tools/snapshot.py` opens Imperialism with read/query access only. The repeatable live check
keeps boot, captures, independent readers, End Turn and cleanup in one PowerShell lifetime:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File harness/prod_snapshot.ps1 -Name snapshot_check1
```

Use a fresh name for each run (the harness refuses to overwrite snapshots). `-Fixture` defaults
to `oil_plant_built`. It captures `before`, a second `idle` snapshot, then `after` one End Turn,
and runs `tools/validate_snapshot.py` against the independent city/tech/diplomacy readers.
`-WarmupTurns N` completes up to 30 turns before the first capture. `-SaveFixture simple_name`
saves the validated after-state as a new `saves/simple_name.imp` (refuses existing names).
`-TracePlanning` traces a fixed list of city planning entries during the measured End Turn;
build `results/trace_calls.exe` first as described in `docs/tracer.md`. Captures happen only
before attachment and after detachment. Trace output stays local under `results/trace_*`.
The `finally` block always stops the game and restores settings. The earlier attempt with
boot and capture in separate command lifetimes found no live game after boot returned;
the single-session harness avoids that observed failure. Its exact cause is not established.

For manual captures with an already running game, use an idle map screen:

```
python -I tools/snapshot.py results/snapshot_before.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File harness/prod_endturn.ps1
python -I tools/snapshot.py results/snapshot_after.json
python -I tools/diff_snapshot.py results/snapshot_before.json results/snapshot_after.json
```

The diff exits 0 for identical captured state, 1 for differences, and fails on unsupported schemas.
`--raw` includes changed byte offsets; `--limit N` limits field and per-block byte details while
preserving total counts. Raw JSON snapshots contain game memory and stay local under the ignored
`results/snapshot*.json` pattern. Always end a game test with `harness/prod_end.ps1`.

Schema 1 stores addresses, sizes and hex bytes under stable block names, plus decoded fields.
It includes non-null nation objects, non-null Great Power cities and their orders,
population managers and worker pools, diplomacy, technology, the trade object and deal lists,
map manager, 6,480 tiles and 384 province records, both global RNG states, and the full game manager.
Sizes come from `classes.tsv`, constructor allocations and existing readers.
Technology is reached directly through 0x6a43d8 (creation and accesses in the local decompile),
avoiding the older reader's vtable heap scan. TCity uses its 724-byte allocation rather than
the old reader's 0x300-byte probe. Great Powers use the common 2404-byte allocation or the
2928-byte AI allocation when identified by the known TAutoGreatPower vtable. Orders use their
actual vtable-specific allocation sizes (76/80/84/92), rather than reading a uniform 84 bytes.
Unknown order vtables fail explicitly.

| State | Bounds / evidence in the local decompile |
|---|---|
| Game (`g_Game` is TSimMgr) | 0x118-byte allocation in 0x49ded0; constructor 0x57b9e0 |
| City orders and population | 0x4b24b0 allocates each order subclass and the 80-byte population manager |
| Three worker pools | 0x4b5c00 allocates 12 bytes each at population +0x10/+0x14/+0x18 |
| Map provinces | 0x50e8b0 allocates 384 records of 0xa8 bytes (+4-byte array cookie) at map +0x10 |
| Trade deals | 0x5b7a90 creates 17 lists at trade +0xaa8; 0x4882c0 copies 16-byte records to separately allocated targets |
| RNG | Distinct globals 0x6a38e8 and 0x6a5aec use multiplier 0x15a4e35 and increment 1 |

Each deal list captures its 24-byte header, live pointer array, and the separately allocated
16-byte records. Capacity beyond the live count is not read. Bounds are checked before
following pointers (capacity limited to 100,000 as a defensive tool limit, not a game rule).

Decoded comparisons cover nation cash, city stock/capacity/orders/workers, diplomacy matrices,
technology known/per-power records and release turns, trade prices/orders/totals/deal counts,
game turn/local power/phase, and both RNG states. Undecoded changes remain visible
as raw block changes. Pointers/padding are not normalized: compare captures within one process
for now. Equality establishes only equality of captured state.

City task chains and auxiliary records at city +0x270/+0x274 are now included; evidence,
embedded-list offsets and validation are in `docs/field_miner.md`. Task vtables select 20/24-byte
allocations, and chain counts/links/tails are checked before a snapshot is saved.

`tools/snapshot_graph.py` follows the following additional roots. These are allocation/link
layouts, not decoded combat or AI rules. Vtables are checked before reading class allocations;
list counts, tail pointers, back links and cycles are checked where the layout provides them.

| State | Layout and evidence |
|---|---|
| Great Power Interior Minister | nation +0x98, 452 bytes; initialization 0x4d8cc0 distinguishes it from Foreign at +0x94 |
| Minister lists | constructor 0x4be8d0: +0x28/+0x2c/+0x190 point to 28-byte headers (head +4, tail +8, count +0xc); +0x18c points to a 32-byte facade with header shifted +4; all nodes 12 bytes |
| Army Manager | global 0x6a3338, 936 bytes, vtable 0x64c928; initialization 0x4a1870/0x4a18f0 |
| Army records | army +4: 24-byte pointer-array header, pointed records 616 bytes; nested record pointers at +0x250/+0x254 are not followed |
| Grouped stacks | army +0xc: 32-byte list facade; TArmyStack is 28 bytes, vtable 0x64ca38, unit count short +0xa, head +0x14; nodes are 8 bytes (unit pointer, next); save/load 0x4a77b0/0x4a7960 |
| Province garrisons | province +0x98 points directly to a TMilitaryUnit chain, not a TArmyStack; 0x4a1f80 walks unit +0x14 |
| Military units | 68 bytes, vtable 0x66eea8, previous +0x10, next +0x14; constructor 0x5c2cb0 |
| National rosters | every nation +0x44: 32-byte list facade with unit-pointer payloads; constructor 0x4d68f0 |
| Navy Manager | global 0x6a43e4, 16 bytes, vtable 0x65c4c8; constructor 0x556590 |
| Global ships | head global 0x6a3edc, 56-byte objects, vtable 0x65c438, next +0x24, previous +0x28; constructor 0x54f500 and load 0x556ad0 |

Minister node values are captured as raw integers/pointers without dereferencing them. Populated
minister lists do not establish populated city-task payloads. Units reached from province and
stack roots are cross-checked against the independent national-roster roots; the validator rejects
placed units absent from the rosters. It reports roster-only units without rejecting them, since
unplaced units may be valid in other scenarios. Repeated unit addresses count only once.

This is a partial oracle. It does not yet follow military missions, task forces/ports,
army-record pointer targets, all province/nation pointer targets, or every manager/global. The heuristic field miner
(`tools/field_miner.py`) and constructor analysis guide the remaining bounds and pointer layouts.
Reads are not atomic; a turn-counter guard rejects
an advancing turn but cannot detect every concurrent write. Do not run during a turn or trace.

Offline validation: `python -I tools/test_snapshot.py` passes seventeen tests using bounded synthetic
memory: economic changes/identity, null manager, all order allocations and unit tail, unknown
order rejection, indirect deal records and bounds, turn race, block removal/schema rejection,
CLI equality/difference exit codes with output limits, task nodes/subclass sizes/cycle rejection,
and city auxiliary record pointers/bounds. Graph tests cover minister header variants, province
unit and ship chains/cycles, army record bounds, stack nodes, shared units across independent
roots, roster-only/placed-only discrepancies, and unknown graph types before full-object reads.

Live validation on 2026-10-31 (`oil_plant_built`, local power 2): the initial smaller capture
passed eight checks; the expanded capture (`results/snapshot_live2_*`, local only) also passed
all eight. The latter captured 490 blocks before and 498 after, with 3,932 decoded fields;
one End Turn changed 266 fields across 188 blocks. Game turn advanced 5 to 6 (city turn 4 to 5),
local cash fell $44,400 to $44,250, and two idle snapshots were byte-identical. These checks
verify capture/diff plumbing, not the correctness of a lifted turn or deterministic replay.
Final run with both RNG states (`snapshot_live3`) passed all eight checks: 491 -> 489 blocks,
3,933 fields, 282 changed fields across 173 blocks. Idle bytes were identical and the same
turn/cash checks passed. The number of live deal records can increase or decrease each turn.

The city-container expansion (`snapshot_fields2`) also passed eight live checks, capturing
3,947 fields and 505 -> 507 blocks. Both new containers were empty in all seven cities;
nonempty traversal has code/disassembly evidence and synthetic tests, but still needs a live fixture.

The military expansion passed ten live checks (the original eight plus before/after national
roster cross-checks). `snapshot_military_later` completed eight warmup turns, then measured
game turn 13 -> 14: 4,125 fields, 1,926 -> 1,965 blocks, 268 changed fields across 242 blocks.
Its 517 military units were present in both the placed-unit and national-roster roots, with
no discrepancy; one global ship was captured. Minister standard lists were populated, while
the army record/grouped-stack lists and city task/auxiliary lists were empty.

The subsequent planning probe (`snapshot_planning2`) also passed all ten checks with idle
identity: 4,125 fields, 1,918 -> 1,901 blocks, 238 changed fields across 225 blocks, the same
517 units before the turn and one ship. The task generation/processing entries did not fire
(`docs/tracer.md`); populated city task traversal remains live-unverified. Variation in AI
decisions between fresh processes is not yet explained or normalized; these runs establish
within-process capture and graph consistency, not deterministic replay.

Saved after-state `saves/military_later.imp` reloaded successfully. Its independent run
`snapshot_fixture_later1` passed all ten checks at game turn 14 -> 15: 1,901 -> 1,937 blocks,
4,125 fields, 262 changed fields across 241 blocks. Before the turn it again contained
517 units with no placed/roster discrepancy and one ship. Game stopped and user settings
restored after every run, including rejected attempts.
