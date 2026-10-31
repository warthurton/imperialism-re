# State snapshots

`tools/snapshot.py` opens Imperialism with read/query access only. The repeatable live check
keeps boot, captures, independent readers, End Turn and cleanup in one PowerShell lifetime:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File harness/prod_snapshot.ps1 -Name snapshot_check1
```

Use a fresh name for each run (the harness refuses to overwrite snapshots). `-Fixture` defaults
to `oil_plant_built`. It captures `before`, a second `idle` snapshot, then `after` one End Turn,
and runs `tools/validate_snapshot.py` against the independent city/tech/diplomacy readers.
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

This is a partial oracle. It does not yet follow military objects, province pointer targets,
city auxiliary objects, all nation pointer targets, or every manager/global. The field miner
and constructor analysis must supply the remaining bounds and pointer layouts. Reads are not atomic; a turn-counter guard rejects
an advancing turn but cannot detect every concurrent write. Do not run during a turn or trace.

Offline validation: `python -I tools/test_snapshot.py` passes eight tests using bounded synthetic
memory: economic changes/identity, null manager, all order allocations and unit tail, unknown
order rejection, indirect deal records and bounds, turn race, block removal/schema rejection,
and CLI equality/difference exit codes with output limits.

Live validation on 2026-10-31 (`oil_plant_built`, local power 2): the initial smaller capture
passed eight checks; the expanded capture (`results/snapshot_live2_*`, local only) also passed
all eight. The latter captured 490 blocks before and 498 after, with 3,932 decoded fields;
one End Turn changed 266 fields across 188 blocks. Game turn advanced 5 to 6 (city turn 4 to 5),
local cash fell $44,400 to $44,250, and two idle snapshots were byte-identical. These checks
verify capture/diff plumbing, not the correctness of a lifted turn or deterministic replay.
Final run with both RNG states (`snapshot_live3`) passed all eight checks: 491 -> 489 blocks,
3,933 fields, 282 changed fields across 173 blocks. Idle bytes were identical and the same
turn/cash checks passed. The number of live deal records can increase or decrease each turn.
