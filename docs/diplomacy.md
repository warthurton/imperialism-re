# Diplomacy and offers (what is decoded, what is not)

Sources: the game manual ("Diplomacy" and "Receiving Trade Offers"), the decompile (`TDiplomacyMgr`, vtable 0x654d90), and numbers read out of the
running game with `tools/readdiplo.py` while making overtures through the real UI. A tested model of the decoded part is `reimpl/diplomacy.c`.
Confidence: **seen** (in play), **code** (read in the decompile only), **guess**.

## The two kinds of offer

1. **Trade offers** (the "Offer Sheet", screen id 8500). After all Great Powers end their turn the world market opens and each country selling
   a commodity you bid on makes you an offer: "Hurshen offers 2 units of Food @ $87/unit", a Purchase box, a "No more offers of Food"
   checkbox, a red REJECT seal and a blue ACCEPT seal; the book on the right gives advice ("Purchase Not Recommended: we have no consulate with
   Hurshen, thus trade serves no diplomatic purpose"). **Escape rejects, Return accepts** (manual hot keys, seen to work with `Post-Key`). Offers
   you decline pass to other bidders. Accepted trades improve relations (manual; seen: AI trades moved scores 90 -> 91).
2. **Diplomatic overtures** (screen id 2008, the right-hand scroll tab "Offer Treaties"): you order them, they are carried out at End Turn.
   Seven scrolls, mirror coordinates: Peace (270,810), Trade Consulate (655,810), Embassy (900,810), War (270,915), Pact (555,915),
   Alliance (770,915), Empire (990,915). Click a scroll, then a country on the map; a marker stays on the country and clicking it again rescinds
   the overture (manual: money is returned). Information tabs on the left: the blue "i" (basic information), treaties (scroll), relationships (document),
   trade policies (ship), Council report. The tab on the far right is Grants (foreign aid); the ship tab is Trade Policies (subsidies, boycotts).

Manual rules (not all checked): Minor Nations always accept Trade Consulate ($500, opens next turn), Embassy ($5,000, needs a consulate), Pact (free,
needs an embassy) and Peace, and never refuse War being declared on them; Empire (colony) is refused unless relations are friendly enough; Great Powers
accept Peace only when it suits them, offer and accept Alliance when disadvantaged; a Great Power joins your Empire only when its position is hopeless.

## The manager's data (`TDiplomacyMgr`, global 0x6a43d0, 6,364 bytes) [seen]

Nations are numbered 0-6 for the Great Powers and 7-22 for the sixteen Minor Nations (`TDiplomacyMgr_IsGreatPower`: index < 7).

| Offset | Type | Meaning |
|---|---|---|
| +0x79c | 23x23 short, symmetric | **relationship score** 0-255 |
| +0xbbe | 23x23 short, symmetric | **treaty status code**; the names are the game's strings 17361 + code: 0 Member of our Empire, 1 Ruler of our Empire, 2 Alliance, 3 Non-Aggression Pact, **4 Peace** (every pair at the start), 5 Member, **6 War** (4 and 6 seen in the matrix in play) |
| +0xfe0 | 23x23 short, symmetric | game turn the status last changed, -1 = never |
| +4 (384 shorts), +0x304 (384 bytes) | | empty at the start (0 and 255); a history of some kind, unknown |
| +0x1886, +0x18a6 | 16 shorts each | filled in during play (values like 3, 4, 96, 100); unknown |
| +0x1402 | 23x23 short | derived flags written by `SetStatus` (2 for allied Great Powers, 0 at war); unknown |

Start of a game (Introductory, 1815, turn 0): every pair has status 4; scores are 90 between a Great Power and anything, 110 between two Minor Nations,
150 between *neighbouring* Minor Nations (the manual: "Minor Nations like their neighbours"), 110 between the human power and its four starting
consulate nations, and 255 / 256 with oneself. `readdiplo.py --full` prints the whole matrices.

## What `SetRelationship` and `SetStatus` do [code, numbers seen]

* `SetRelationship(a,b,v)` (vf10): symmetric write; negative becomes 0; above 255 becomes 255 (except a == b); **below 50 is allowed only while at war**,
  otherwise it is raised to 50. Human Great Powers are told about the change.
* `SetStatusEx(a,b,code,flag)` (vf29) / `SetStatus` (vf30): writes both halves of the status matrix, stamps the turn into both halves of +0xfe0, tells each
  side if it is a Great Power, then acts on the code: 2 raises the score by 10 (event 0x1a), 3 raises it by 10, 4 lifts it to at least 50, 5 sets it to 255,
  6 starts a war (event 0x19; each nation's slot-18 handler gets 300). The decompiled switch is scrambled by register reuse, so the exact fall-through is a guess.
* `RelationshipLevel(a,b)` (vf26): the score as the 8-level colour code on the diplomacy screen: below 21 -> 0, 50 -> 1, 80 -> 2, 101 -> 3, 136 -> 4, 171 -> 5, 206 -> 6, up to 240 -> 7, above -> 8.
  So the start scores 90 / 110 / 150 / 255 are levels 3 / 4 / 5 / 8, and war's 40 and 50 are levels 1 and 2 (the manual: "dark green means they might join your Empire").
* `IsAtWar` is `status == 6`; `CountAllies(n)` counts the Great Powers whose status with n is 2.
* A Minor Nation answers a Great Power's overtures in `TMinor_HandleOffer` by message id: 0x12d (aid or bribe), 0x12f (status 3), 0x130 (status 4),
  each charging an amount.

## Pending overtures live in the Great Power's own object [seen]

Snapshots of all 23 nation objects (`tools/readnations.py`) before and after ordering showed that the only nation that changed was the local Great Power:
cash at +0x10 (50,000 -> 49,500 for the consulate) and a **table of pending overtures at about +0xb2, one short per target nation** (entry for nation n at
+0xb2 + 2n, -1 = none). Ordering War on Pram (nation 11) wrote 305 (0x131) at +0xc8; ordering a Trade Consulate in Manx (nation 13) wrote 307 (0x133) at +0xcc;
both were back to 0xFFFF after End Turn. So the overture order ids are 0x131 = War and 0x133 = Trade Consulate; `TMinor_HandleOffer` receives 0x12f and 0x130, which fits Pact
(status 3) and Peace (status 4) in a sequence 0x12d Empire?, 0x12f Pact, 0x130 Peace, 0x131 War (the others not yet seen). Every nation also changes +0x8c / +0x8e each
tick (a clock): ignore it when diffing.

## Experiment: overtures from the real UI (fixture `oil_t0`, local power index 2)

| Overture (ordered turn 1-2) | Money | Matrices before End Turn | After End Turn |
|---|---|---|---|
| Trade Consulate in Manx | $500 taken **at once** (50,000 -> 49,500) | nothing changed | consulate shown on the map next turn; **no cell of the three matrices changed** |
| Embassy in Manx | $5,000 at once (49,350 -> 44,350) | nothing changed | marker shown; no matrix change |
| War on Pram (nation 11) | free | nothing changed | status G2-M11 **4 -> 6**, turn stamp -1 -> 2; scores: **Pram 90 -> 40**, three of its neighbours **90 -> 50**, every other Minor Nation **-9** (90 -> 81, 110 -> 101); Great Powers' scores to the human unchanged |
| (no overture) | | | AI Great Powers' trades raised their scores with minors by 1-2 per turn |

So overtures are **queued as orders** until End Turn (pending ones are not in the manager), consulates and embassies are **not stored in these matrices**,
and the war declaration's score ripple (-50 target, -40 neighbours, -9 others) is real but its code has **not been found**: it is not in `SetStatus`,
`TMinor_HandleOffer` or `TClientGreatPower_vf20` (which turned out to be the "Great Power conquered" handler). `TRemoteMinor_vf50` is the "foreign units must
leave" step of a war. The relationship numbers 81 / 50 / 40 were seen once and only for a war on a Minor Nation.

## Open

* How End Turn turns a pending order (0x131 War, 0x133 Consulate, ...) into the change: the table is at +0xb2 of the Great Power; find who reads it (search for `+ 0xb2` /
  `+ 0xc8` accesses on the nation, and the Great Power's virtual slots around 0x2a8-0x2b0).
* The order ids of Embassy, Pact, Peace, Alliance and Empire (order each once and read the table).
* Where consulates and embassies are stored (candidates: the Minor Nation object's per-nation table at +0x14, or the Great Power object).
* The war ripple, the acceptance rules for Pact, Empire and Peace, and what Alliance does on the Great Power side.
* Status codes 0, 1, 3 and 5 as the game uses them (only 4 and 6 were seen).
* The trade Offer Sheet's logic (`TTradeMgr_SettleTrades` pairs each offer with every allowed buyer after diplomacy checks) is read but not tested in play.
