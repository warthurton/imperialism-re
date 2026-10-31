# Object field candidates

`tools/field_miner.py` indexes typed memory accesses in the local decompile. It does not
generate C structs or assign field meanings. Run from the repository root:

```
python -I tools/field_miner.py
python -I tools/field_miner.py --object TCity --output results/fields_city.tsv
python -I tools/test_field_miner.py
```

The defaults read `imperialism_named.c` and `classes.tsv`, and write `results/fields.tsv`.
`--source` and `--classes` accept alternate inputs. Generated reports stay local under
`results/fields*.tsv`; they contain offsets, widths, counts, function addresses/names and
provenance, with no source snippets. Functions below 0x410000 (incremental-link stubs) are
excluded to avoid counting duplicated thunk bodies.

Each row describes one object/path, constant offset, access width, dynamic-index flag and
provenance. Read, write and address-taking counts remain separate; a compound assignment
counts as both a read and a write. Different widths at the same offset remain separate.
`functions` lists the functions that supply the evidence. Counts are static occurrences,
not execution counts from the tracer.

The parser tokenizes balanced expressions, handles primitive casts and simple additions,
and respects the declared arithmetic type: adding 3 to an `int *` advances 12 bytes, while
casting that pointer to an integer first makes the addition advance 3 bytes. Parameter types
come from the signature. Named instance methods supply a likely class attribution for
`param_1`; unidentified functions keep an address-qualified parameter label. Static functions
do not acquire a class attribution merely because their names begin with a class name.

Nested pointer targets get their own path. A read through a pointer stored at city +8 goes
under `TCity->+0x8`; it is not merged into the city's own fields. Unknown global arithmetic
stays marked `unknown_stride_units`, and an unresolved parent path stays unresolved even
if a later offset is known in bytes. Dynamic indices remain separate from fixed fields.
Only the established nation pointer tables have built-in global element widths.

`allocation_size` comes from `classes.tsv` for directly attributed classes.
`within_allocation` is blank when no fixed comparison can be made. A false value is a review
candidate, not permission to enlarge the object: the class attribution, Ghidra type or
allocation table may be wrong. Passing the bound is also not proof of a correct field.

The first full run on 2026-10-31 analyzed 8,779 functions and produced 8,702 candidate rows
across 2,521 object/path labels. There were 263 unresolved rows, 592 dynamically indexed
rows and one declaration-bound conflict (a library `CControlBar` access). The city selection
contains 82 rows across seven paths, six dynamic rows and no declaration-bound conflict.
Eleven synthetic tests cover scaling/cast order, access modes, binary bitwise-and versus
address-taking, arrays/dynamic indices,
address-taking, nested targets, unknown scaling, negative offsets, comments/literals,
static-method attribution, aggregation/stub exclusion, and bounds.

The output is deliberately incomplete. It does not follow local aliases, interprocedural
types, control flow, implicit register arguments, arbitrary pointer expressions, scalar
global accesses or every untyped dereference. Decompiler errors remain possible even for
resolved byte offsets. Check constructors, save/load code and machine code before extending
the live snapshot reader. Do not turn these candidates directly into trusted layouts.

## First snapshot expansion

The city report identified two uncaptured pointers: +0x270 (32-byte task list) and +0x274
(24-byte pointer-record list). Constructor 0x4b2570 and city save/load methods 0x4b35d0 /
0x4b30a0 establish that both containers belong to the city.

The task list embeds a standard list at +4. This detail was lost in the decompile's implicit
`this` arguments: the first live attempt rejected the misinterpreted header, then machine
code at 0x5aebb5 confirmed that the standard-list constructor receives object +4. Head, tail
and count are therefore at task-list +8/+0xc/+0x10. Nodes are 12 bytes (next, previous, task
pointer), with 20-byte city tasks or 24-byte ship-building tasks selected by their known
vtables. The reader validates counts, links, tails and task types before saving a snapshot.

The second container holds pointers to separately allocated four-byte records. Its meaning
is not assigned; the reader captures the header, live pointers and record bytes. Counts are
bounded by the same defensive tool limit as trade lists (100,000; not a game rule).

Live run `snapshot_fields2` passed all eight existing checks: 505 -> 507 blocks, 3,947 decoded
fields, 269 field changes across 173 blocks, game turn 5 -> 6 and local cash $44,400 -> $44,250.
Idle captures were byte-identical. All task/auxiliary record counts were zero in this fixture,
so nonempty traversal remains verified only by synthetic tests and code/disassembly review.
Ten snapshot tests pass; populated live fixtures remain a next step. Game stopped and user
settings restored after both the rejected run and the successful run.
