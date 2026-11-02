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
  | +0x1c | structure flags: 0x04 port, 0x10 depot, 0x20 town, 0x08 national capital (0x01 / 0x02: other town bits, a guess). Ordinary town 34, minor capital 41, Great Power capital 63 (town + capital + port + depot), built depot 34 -> 50, built port 0 -> 4 | confirmed (7 + 16 capitals, my two ports, AI port and depot appearing in a turn diff) |
  | +0x06 | true rail mask: bit 0 NE, 1 E, 2 SE, 3 SW, 4 W, 5 NW; odd rows are shifted half a tile right (odd row: NE = (x+1,y-1), NW = (x,y-1), SE = (x+1,y+1), SW = (x,y+1); even row: NE = (x,y-1), NW = (x-1,y-1), SE = (x,y+1), SW = (x-1,y+1)); both ends of a piece carry opposite bits | confirmed: all 36 rail links in the world are reciprocal, and my capital-to-port line reads 1, 40, 4 |
  | +0x17 | the same rail mask **as the local player can see it**: equal to +0x06 on my rail, 0 on all AI rail (20 tiles differ), a fog-of-war copy | likely (pattern only; test by scouting) |
  | +0x05 | id of the structure (depot, port, capital) that gathers the tile, 255 = none; a structure claims its own tile and the neighbouring land tiles not already claimed (my capital 4, timber port 2, fish port 3) | confirmed pattern; the numbering is unknown |
  | +0x0c, +0x0d, +0x02, +0x16, +0x19, +0x1e | undecoded (+0x0c = 1 on the capital and two coastal neighbours) | open |
  | +0x03 = +0x04 | 0-80, always equal | unknown (art variant?) |
* **Rule for autoplay (decided by the user, 2026-11-01)**: when we are just playing the game, use **player-visible information only**: prospected tiles (the `prospected` flag), the deposit icons the toolbar shows, what is on screen.
  The unprospected deposits (and any other hidden data) are readable from memory, and may be used **only to test something specific faster** (a fixture, a decode, a rule check), never while playing. `readmap.py find ... --unprospected` is such a test aid.
* **How it was checked**: per-offset histograms of the 6,480 tiles; the owner map rebuilt from provinces (my country lies at x 44-57, y 39-56 with sea to its west, as on screen); a turn-end diff (152 tiles changed, mostly the
  scrolled window and moving units); the unit pointers of my 7 civilians.
* **Controlled Engineer experiment (2026-11-01)**: one Engineer ordered rail from (47,48) into the empty plain (47,49) for $100 and the turn was ended. Tile diff: (47,48) `+06` 40 -> 44 (adds bit 2, SE) and (47,49) `+06` 0 -> 32 (adds bit 5, NW), the visible mask `+17` changed the same way, `+05` already 4 on the new tile, nothing else on my side changed. This confirms the rail mask and the staggered geometry directly. The unit pointer (`+0x20..0x23`) moved with the Engineer.
  Clicking that Engineer's tile afterwards gave an **empty** construction popup (no depot, no port): a tile the capital already gathers (`+05` = its id) offers nothing to build. The depot half (flag `0x10` appearing, gatherer claims spreading) was **not** run: the game then crashed (see `docs/screens.md`, modal popups) and the rerun was stopped.
* **Open**: whether a depot is "connected" (the green/red lights; probably derived from rail reaching the capital, not stored per tile), fog for ports and depots; the capital's tile; developed levels (the Farmer / Miner / Forester level of a tile); per-tile unit object layout (type, order, cycle order); fog.
