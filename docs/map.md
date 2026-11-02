# The map in memory (decoded 2026-11-01 from the running game, fixture `play_fall1817`)

`tools/readmap.py` reads it (read-only); `docs/snapshots.md` covers the raw capture. Global `g_MapMgr` = pointer at 0x6a43d4.

* **Grid**: 6,480 tiles = **108 wide x 60 high**, `index = y * 108 + x` (the code divides and takes the remainder by 0x6c everywhere; rendering the grid gives a recognisable world with mountain ranges and coasts).
  Tiles are 0x24 bytes at map +0xc; provinces are 120 used records (384 allocated) of 0xa8 bytes at map +0x10.
* **Provinces**: byte +0 and +1 = owning nation (equal for the whole saved game; 0-6 Great Powers, 7-22 minors; the local power is the one in `readcity.py`'s "client powers"), short +4 = the town's tile index,
  +0x0a... = neighbour province indices (0xffff = none), 8 provinces per Great Power and 4 per minor. Tile short +0x14 = province index (0xffff on the sea).
* **Tile fields**
  | Offset | Meaning | Status |
  |---|---|---|
  | +0x00 | terrain: 0 plain, 1 forest, 2 hills, 3 mountain, 4 and 6 oil-bearing (swamp / desert / tundra, which is which is open), 5 sea, 7 farmland | confirmed (counts, card tables, code compares 5 = sea) |
  | +0x13 | kind: 1 dry plains, 2 plantation, 3 open range, 4 horse ranch, 5 farm, 6 orchard, 7 fertile hills, 8 barren hills, 9 mountain, 10 / 11 / 12 oil terrain, 13 scrub forest, 15 hardwood forest | confirmed by cross-tab with the card tables |
  | +0x11, +0x12 | two resource slots (signed byte, -1 = none): 0 cotton, 1 wool, 2 timber, 3 coal, 4 iron, 5 horses, 6 oil, 17 grain, 18 fruit, 19 fish, 20 livestock, 21 gold, 22 gems | confirmed (code in `TMinor_TallyMapResources`; deposits sit here before they are prospected) |
  | +0x01 bit 0 | prospected flag | confirmed on my mountains |
  | +0x20 (dword) | pointer to the unit on the tile (vtable 0x66ee60 for my civilians; moves with the unit) | confirmed by a moving unit |
  | +0x10 | index inside the visible window (9 x 8 tiles): changes when the map scrolls, **not game state** | confirmed (the user scrolled the view; 72 tiles renumbered) |
  | +0x05, +0x06, +0x17, +0x1c, +0x0c, +0x0d, +0x02, +0x16 | probably gatherer / structure / rail / level fields: +0x05 changed 255 -> 1..3 on small clusters of tiles when AI or I built something, +0x1c rose 34 -> 50 on one tile | **undecoded**: next, diff before/after an Engineer builds a depot, a port and rail |
  | +0x03 = +0x04 | 0-80, always equal | unknown (art variant?) |
* **Caution for autoplay**: the unprospected deposits (and the gems and iron under a mountain) are readable from memory before the player would know them. That is legal for a test bot but not what a player sees: decide
  whether an autoplayer should use them or only prospected tiles (`prospected` flag) and the deposit icons the Prospector toolbar already shows.
* **How it was checked**: per-offset histograms of the 6,480 tiles; the owner map rebuilt from provinces (my country lies at x 44-57, y 39-56 with sea to its west, as on screen); a turn-end diff (152 tiles changed, mostly the
  scrolled window and moving units); the unit pointers of my 7 civilians.
* **Open**: structures (depot, port, rail) and their "connected" state; the capital's tile; developed levels (the Farmer / Miner / Forester level of a tile); per-tile unit object layout (type, order, cycle order); fog.
