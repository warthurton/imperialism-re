# Technology: the Invest in Technology screen (screen id 2300)

Seen in the real game (fixture `oil_plant_built`, text log and memory), 2026-10-31.

* **The microscope button ("Invest in Technology", map toolbar, (1133,80) mirror units) and hot key 5 open the same screen** (id 2300, `TScreenBuilder_TechHistory` / `TTechHistoryView`): columns
  Technologies / Cost / Benefits, one row per technology with its picture, name, year offered, a cost cell and the benefit text. Earlier notes called it "only the history": it is also where techs are bought.
* **The cost cell has three states**: a **price button** (the tech can be bought now, e.g. Cotton Gin `$1,000`), **"Purchasing"** (bought this turn, still in progress), and **"Purchased in <year>"**. Game strings for the others:
  `Requires [tech] and [tech]` / `Requires [tech]` (prerequisites not met), string ids 23261-23268.
* **Buying**: one click on the price button. The cash is charged at once ($44,400 -> $43,400; the top-bar figure and the Owner cash both read it), the button reads "Purchasing", and the title bar changes to "Purchase Technology"
  (the click is not asked to be confirmed). At End Turn it becomes "Purchased in 1816" (the year of the turn it completes in). A purchased tech is not charged again. The `TTechMgr` known-tech array (+0x180) already showed four known techs
  when read during "Purchasing" and did not change at End Turn, so the known flag is set when the order is placed or the new tech is stored elsewhere; I did not capture a before/after of the array.
* **What was on offer** (turn 4, Spring 1816, no poked techs except Oil Drilling for the local power): High Pressure Steam Engine 1815 and Seed Drill 1815 (already purchased), Cotton Gin 1816 (`$1,000`, benefit "Allows
  Farmers to improve Cotton plantations to Level I"). **Nothing new appeared by Spring 1817** (4 turns per year), so techs are not simply released by the calendar; the "Requires ..." strings suggest a prerequisite chain.
  Oil Drilling does not show on this screen at all in that fixture (it was poked into the record, not bought).
* Not looked at: what unlocks the next entries, how the price is set (Cotton Gin $1,000), whether Great Powers' research changes the list, what the benefit does in play (Farmers' Level I), insufficient cash behaviour.
* Memory: `tools/readtech.py` finds `TTechMgr` by vtable 0x66ad28 (the old default 0x66ac98 matched nothing and was fixed).
