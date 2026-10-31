# Technology: the Invest in Technology screen (screen id 2300)

Seen in the real game (fixture `oil_plant_built`, text log and memory), 2026-10-31.

* **The microscope button ("Invest in Technology", map toolbar, (1133,80) mirror units) and hot key 5 open the same screen** (id 2300, `TScreenBuilder_TechHistory` / `TTechHistoryView`): columns
  Technologies / Cost / Benefits, one row per technology with its picture, name, year offered, a cost cell and the benefit text. Earlier notes called it "only the history": it is also where techs are bought.
* **The cost cell has three states**: a **price button** (the tech can be bought now, e.g. Cotton Gin `$1,000`), **"Purchasing"** (bought this turn, still in progress), and **"Purchased in <year>"**. Game strings for the others:
  `Requires [tech] and [tech]` / `Requires [tech]` (prerequisites not met), string ids 23261-23268.
* **Buying**: one click on the price button. The cash is charged at once ($44,400 -> $43,400; the top-bar figure and the Owner cash both read it), the button reads "Purchasing", and the title bar changes to "Purchase Technology"
  (the click is not asked to be confirmed). At End Turn it becomes "Purchased in 1816" (the year of the turn it completes in). A purchased tech is not charged again. The `TTechMgr` known-tech array (+0x180) already showed four known techs
  when read during "Purchasing" and did not change at End Turn, so the known flag is set when the order is placed or the new tech is stored elsewhere; I did not capture a before/after of the array.
* **What unlocks a tech: the calendar, not prerequisites.** At game start `FUN_005af330` draws, for each of techs 3-28, a random release turn inside a fixed window (4 turns per year, turn 0 = Spring 1815) and stores it
  in `TTechMgr` +0x0a + 2*(tech-3). Each turn, in sim phase 0x11, `FUN_005af980` compares every unreleased tech's turn with the game's turn counter (`g_Game`+0x2c, which is one ahead of the city's turn counter at
  `city+0xc` while you read it between turns); on a match `FUN_005afba0` sets the global known flag (`TTechMgr` +0x180 + tech), records it as the latest discovery (+0x262) and the newspaper prints "New Invention: <tech>"
  (plus a short article). Techs 0-2 are known from the start. A released tech is then offered to every power as a price button; buying runs `FUN_005afd00(tech, power)`, which sets the power's record (+0x268 + power*29 + tech) to 2
  and applies the effects (farm/mine levels, new units and ships, buildings). The game strings `Requires [tech] ...` exist but this release rule has no prerequisite check, so a tech can be released before ones it "follows".
* **The schedule** (table at 0x66ab9a read with `tools/dump_techtable.py`; window = the random draw's range; price table at 0x66aaf4 indexed from tech 3). The window lists years as the in-game date at release:

| Tech id | Technology | Release window | Price |
|---|---|---|---|
| 3 | Cotton Gin | 1816-1820 (turns 4-20) | $1,000 |
| 4 | Streamlined Hulls | 1821-1825 (turns 24-40) | $1,500 |
| 5 | Square-Set Timbering | 1821-1825 (turns 24-40) | $1,500 |
| 6 | Iron Railroad Bridge | 1821-1825 (turns 24-40) | $1,500 |
| 7 | Feed Grasses | 1821-1825 (turns 24-40) | $1,500 |
| 8 | Spinning Jenny | 1826-1830 (turns 44-60) | $3,000 |
| 9 | Paddlewheels | 1826-1830 (turns 44-60) | $3,000 |
| 10 | Steel Plows | 1831-1835 (turns 64-80) | $3,000 |
| 11 | Bessemer Converter | 1836-1840 (turns 84-100) | $6,000 |
| 12 | Compound Steam Engine | 1836-1840 (turns 84-100) | $7,000 |
| 13 | Rifled Artillery | 1841-1845 (turns 104-120) | $10,000 |
| 14 | Breech-Loading Rifles | 1841-1845 (turns 104-120) | $12,000 |
| 15 | Advanced Iron Working | 1846-1850 (turns 124-140) | $12,000 |
| 16 | Power Loom | 1846-1850 (turns 124-140) | $12,000 |
| 17 | Mechanical Reaper | 1851-1855 (turns 144-160) | $12,000 |
| 18 | Commercial Fertilizer | 1856-1860 (turns 164-180) | $12,000 |
| 19 | Oil Drilling | 1856-1860 (turns 164-180) | $25,000 |
| 20 | Barbed Wire | 1861-1865 (turns 184-200) | $20,000 |
| 21 | Steel Armor Plate | 1866-1870 (turns 204-220) | $40,000 |
| 22 | Large Artillery | 1871-1875 (turns 224-240) | $40,000 |
| 23 | Dynamite | 1871-1875 (turns 224-240) | $40,000 |
| 24 | Marine Engineering | 1871-1875 (turns 224-240) | $40,000 |
| 25 | Machine Guns | 1876-1880 (turns 244-260) | $100,000 |
| 26 | Chemistry | 1876-1880 (turns 244-260) | $120,000 |
| 27 | Improved Range-Finding | 1881-1885 (turns 264-280) | $150,000 |
| 28 | Internal Combustion | 1881-1885 (turns 264-280) | $150,000 |

  The Cotton Gin is the only tech that can be released before 1821, so a new game offers nothing new between the Cotton Gin and 1821. Price and window rows were read from the exe; the Cotton Gin ($1,000) and
  Streamlined Hulls ($1,500) prices were checked in play, and every release turn drawn in the test world fell inside its window (`tools/poke_techturn.py` with no arguments prints them).
* **Test in play** (fixture `oil_plant_built`, turn counter 4-8): the real schedule had Streamlined Hulls at turn 36. `tools/poke_techturn.py 4 8` (a fixture poke, a different turn written into the slot) moved it; after the End Turn
  that made the counter match, the newspaper announced "New Invention: Streamlined Hulls" and the screen showed a `$1,500` button with year 1817. Buying it charged $1,500 at once; one turn later the Shipyard dialog gained a fifth ship,
  the **Clipper** (Hull 25, Cargo 4, no weapons, cost 2 Fabric + 6 Lumber, "more likely than other ships to run a blockade or escape hostile fleets").
* Not tested: the other techs' effects, what the AI powers do (the per-power record is set for each power; `FUN_005af980` also charges and sets a timer for powers that have not got a known tech, which I did not trace), the
  1-turn purchase delay for other techs (here the "Purchasing" state lasted one End Turn), insufficient cash.
* Memory: `tools/readtech.py` finds `TTechMgr` by vtable 0x66ad28 (the old default 0x66ac98 matched nothing and was fixed).
