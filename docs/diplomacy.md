# Diplomacy and offers (what is decoded, what is not)

Sources: the game manual ("Diplomacy" and "Receiving Trade Offers"), the decompile (`TDiplomacyMgr`, vtable 0x654d90), the game's own strings, and numbers read
out of the running game (`tools/readdiplo.py`, `readnations.py`, `readpending.py`) while ordering every overture through the real UI. A tested model of the decoded
part is `reimpl/diplomacy.c`. Confidence: **seen** (in play), **code** (read in the decompile only), **guess**.

## The two kinds of offer

1. **Trade offers** (the "Offer Sheet", screen id 8500). After all Great Powers end their turn the world market opens and each country selling a commodity you bid on
   makes you an offer: "Hurshen offers 2 units of Food @ $87/unit", a Purchase box, a "No more offers of Food" checkbox, a red REJECT and a blue ACCEPT seal; the book
   on the right gives advice. **Escape rejects, Return accepts** (seen with `Post-Key`). Declined offers pass to other bidders. Accepted trades improve relations (manual;
   seen: AI trades moved scores 90 -> 91). End Turn then shows the trade results book (id 8800) and the Imperial Times (id 8451).
2. **Diplomatic overtures** (screen id 2008, the right-hand scroll tab "Offer Treaties"): ordered during the turn, carried out at End Turn. Seven scrolls, mirror coordinates:
   Peace (270,810), Trade Consulate (655,810), Embassy (900,810), War (270,915), Pact (555,915), Alliance (770,915), Empire (990,915). Click a scroll, then a country; a
   marker stays and clicking it again rescinds the order (money returned). Left tabs: the blue "i" (information), treaties (scroll), relationships (document), trade
   policies (ship), Council report. Far right: Grants (foreign aid) and Trade Policies (subsidies, boycotts).

Manual rules (not all checked): Minor Nations always accept Trade Consulate, Embassy (needs a consulate), Pact (needs an embassy) and Peace, and cannot refuse War;
Empire (colony) is refused unless relations are friendly enough; Great Powers accept Peace only when it suits them, offer and accept Alliance when disadvantaged.

## `TDiplomacyMgr` (global 0x6a43d0, 6,364 bytes) [seen]

Nations are numbered 0-6 (Great Powers) and 7-22 (Minor Nations). Four symmetric 23x23 short matrices:

| Offset | Meaning |
|---|---|
| +0x79c | **relationship score** 0-255 |
| +0xbbe | **treaty status**, named by the game's strings 17361 + code: 0 Member of our Empire, 1 Ruler of our Empire, 2 Alliance, 3 Non-Aggression Pact, **4 Peace** (every pair at the start), 5 Member, **6 War** |
| +0xfe0 | game turn the status last changed (-1 = never) |
| +0x1402 | **diplomatic presence**: 0 none, **1 Trade Consulate, 2 Embassy**. At the start: 2 between the Great Powers, 1 for the human power in four Minor Nations (the AI powers also hold consulates) |

Also: 16-entry short tables at +0x1886 (the Great Power with the **best relationship** with each Minor Nation) and +0x18a6 (its **favourite trading partner**), both indexed by
nation number (entries 0-6 unused), filled by `UpdateMinorFavourites` after trade; 384-entry tables at +4 and +0x304 (empty at the start, unknown); the war list object at +0x18d4.
Per Great Power object (`g_Nations[g]`): a **pending-overture table at +0xb2** (one short per target, 0xFFFF = none), a second table at +0xe0 (aid amounts and notices), an
attitude table at +0x14 (100 normal, **300 = war**).

Start of a game (Introductory, 1815): scores 90 between a Great Power and anyone, 110 between two Minor Nations, 150 between *neighbouring* Minor Nations, 110 between the
human power and its four consulate nations, 255 / 256 with oneself. `readdiplo.py --full` prints the matrices.

## Overture order ids and costs [seen]

The id written into the pending table when you click a country (read with `tools/readpending.py`):

| Overture | Id | Cost | Effect at End Turn (`TDiplomacyMgr_ExecuteOvertures`, seen unless noted) |
|---|---|---|---|
| Empire | 0x12d (guess; not offered at the relationship tried) | | delivered to the target (`TMinor_HandleOffer`) |
| Alliance | 0x12e = 302 | free | delivered to the target; a Great Power may refuse (Kem did: no status change) |
| Pact | 0x12f = 303 | free | delivered to a Minor Nation, which accepts: **status 4 -> 3, score +10** |
| Peace | 0x130 = 304 | free | delivered: **status 6 -> 4, score raised to 50** |
| War | 0x131 = 305 | free | not at war yet -> `DeclareWar` (status 6, turn stamp; scores fall: see below) |
| Trade Consulate | 0x133 = 307 | **$500 at once** | presence 1 |
| Embassy | 0x134 = 308 | **$5,000 at once** | presence 2 |

`TClientGreatPower_PlaceOverture` (vf116) commits an order: writes the id at +0xb2 + 2*target, charges the cost; id -1 cancels and refunds. The table is cleared at End Turn.

## The rules in the code

* `SetRelationship(a,b,v)`: symmetric; negative -> 0; above 255 -> 255 (except a == b); **below 50 only while at war**, otherwise raised to 50.
* `SetStatus(a,b,code)`: writes both halves of the status matrix, stamps the turn, tells each Great Power side, then by code: 2 and 3 add 10 to the score, 4 lifts it to at least 50,
  5 sets 255, 6 clears the presence entry and starts the war. (The decompiled switch is scrambled; the pact and peace effects were seen, the rest is code.)
* `RelationshipLevel(a,b)`: the colour code, 8 levels: below 21 -> 0, 50 -> 1, 80 -> 2, 101 -> 3, 136 -> 4, 171 -> 5, 206 -> 6, up to 240 -> 7, above -> 8.
* `ExecuteAid` (code, not seen): with an embassy, a grant of $1,000 adds 2 to the score, $3,000 adds 4, $5,000 adds 6, $10,000 adds 10.
* `UpdateMinorFavourites` (after trade): for each Minor Nation, among Great Powers with presence > 0, the best relationship and the favourite trading partner
  (max of (200 - the power's attitude entry) x score), ties broken by the game's LCG; a power that loses a position gets message 0x13a / 0x13b.
* `IsAtWar` is `status == 6`; `CountAllies(n)` counts Great Powers with status 2.

## Experiments (fixture `oil_t0`, local power 2)

| Order | Seen |
|---|---|
| Consulate Manx, Embassy Dedge, War Pram, Alliance Kem (turn 1) | cash -$500 and -$5,000 at once; ids 0x133, 0x134, 0x131, 0x12e in the table; at End Turn presence Manx 1, Dedge 2; war status G2-M11 4 -> 6, turn 1; Kem did not ally |
| War on Pram, scores | Pram 90 -> **40**, three of its neighbours 90 -> 50, every other Minor Nation **-9** (90 -> 81, 110 -> 101); Great Powers' scores unchanged |
| Pact Dedge, Peace Pram (turn 2) | ids 0x12f, 0x130; status G2-M19 4 -> 3 (score 101 -> 111), G2-M11 6 -> 4 (score 40 -> 50); no cash change |
| no overture | AI trades raised their scores with minors by 1-2 per turn |

## Open

* **The war ripple** (-50 target, -40 its neighbours, -9 other minors): not in `SetStatus`, `DeclareWar`, `ExecuteOvertures`, `TClientGreatPower_vf161/vf164`, `TRemoteMinor_vf18/vf50`
  or the news poster `FUN_0055c9f0`. Seen once, for a war on a Minor Nation. Next: the nation-side handlers (`+0x2a8`, `+0x214`, `+0x1d4`) and the events 0x19 / 0x1a consumers.
* The Empire overture's id (0x12d is a guess) and the conditions under which it is offered; what accepting an Alliance does on the Great Power side.
* Aid: the Grants tab, the second table at +0xe0, and the effect seen in play.
* Status codes 0, 1 and 5 as the game uses them (Empire); the war list at +0x18d4.
* The trade Offer Sheet's logic (`TTradeMgr_SettleTrades` pairs each offer with every allowed buyer after diplomacy checks) is read but not tested in play.
