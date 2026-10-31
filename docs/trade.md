# Trade in play: Board of Trade, Offer Sheets, merchant marine

Seen in the real game (fixture `oil_plant_built`, Winter 1817 to Summer 1817), with the shim's text log. Model: `reimpl/trade.c`, self-tested.
Code side (read, not tested): `TTradeMgr_SettleTrades`, `TTradeMgr_CollectGreatPowerOrders`; the manual's "Bid and Offers screen" chapter (p. 61-69).

## The Board of Trade (hot key 3, screen id 2009)
15 commodity rows in fixed order: Clothing, Furniture, Hardware, Arms, Food, Fabric, Lumber, Paper, Steel, Cotton, Wool, Timber, Coal, Iron, Horses. Columns: Price (last
turn's world price), Available (warehouse stock not already ordered into production; "--" when none), Quantity to Offer. Two brass loops per row (mirror units):
the **Bid** loop at about x=290 and the **Offer** loop at about x=452; row y = 245 + 40 per row down to Arms, then 407 (Food) + 40 per row... (read the screenshot; Hardware 325,
Coal 727, Iron 767). Clicking an open bar closes it (the Bid bar's end tab at x=396).
* **Four bids at most**: a fifth click on a closed Bid loop did nothing (Coal), then worked after Cotton's bid was closed.
* Offers: the quantity slider defaults to the whole stock (10 Hardware); no limit on how many goods are offered. Both bids and offers are remembered next turn.

## Settlement (End Turn)
After the Great Powers end their turns the world market opens: one **Offer Sheet** (id 8500) per deal, e.g. "Sindel offers 2 units of Food @ $67 / unit.", with Purchase,
"No more offers of Food" and a hint panel ("Purchase Recommended: We have a Consulate with Sindel, thus each trade improves our relationship with them. Industry does not need
more Food. A purchase of merely one unit will provide the diplomatic benefits of a trade deal."; "Not Recommended ... no consulate with Pont"). Return accepts at the offered quantity,
Escape rejects. Then the results book (id 8800: Sold, Bought, Military Upkeep, Overseas Profits, Bottom Line, "Credit Limit =") and the Imperial Times (8451).

Three turns (cash is the bottom line exactly: before + sold - bought - 150 upkeep = after):

| Turn | Orders | Deals seen | Bottom line |
|---|---|---|---|
| Winter 1817 | offer 10 Hardware; bids Food, Wool, Timber, Coal | sold 10 Hardware to Pont @ $1,191; Food offers from Hurshen, Sindel, Pont, 2 units @ $67, all accepted (+6 Food); **no** Coal/Timber/Wool sheets | +$11,910 - $402 - $150 = $11,358 |
| Spring 1817 | bids Wool, Timber, Coal, Iron | Wool 1 (Zinlu), Coal 6 @ $122 (Dedge), Iron 2 + 2 @ $127 (Sindel, Bruhr) | -$1,490 |
| Summer 1817 | offer 10 Clothing + 10 Furniture; the same four bids | sold 10 Clothing to Bruhr @ $1,179 and **6** Furniture to Sindel @ $1,130 (4 left); bought nothing | +$18,570 - $150 = $18,420 |

## Merchant marine limits the whole turn
The ship icon on the board reads **16**. Each unit sold or bought uses one; deals are taken in board order, and when the 16 are used up nothing else reaches you: Winter 1817 used
10 Hardware + 6 Food, and the Coal, Timber and Wool offers never arrived (the results book still lists who offered to sell us Coal/Timber/Wool); Summer 1817 used 10 + 6 on the sale
and the four bids got nothing. So the order of the board (finished goods first, then food, then raw materials) decides what you get when you both sell and buy.
Prices move with the deals (Hardware 1,204 -> 1,191 -> 1,170..., Food 72 -> 67); each Offer Sheet is priced at the board price.

## Still open
Who is "first in line" (the favourite-trader table at `TDiplomacyMgr` +0x18a6 is the likely rule), how the price update works, the Deal Book/Trade Book tabs, the ship purchase
(merchant marine grows through the Shipyard: +2 per Trader, 16 -> 20 seen, see production_playtest.md), and whether a bid that finds no offer carries over. Read from code only: the offer-sheet settlement order and the price formula.
Harness: `harness/prod_endturn.ps1 -Accept` accepts every offer and prints each sheet's text.

## Code notes (read from the decompile, not checked in play)
* `TTradeMgr_SettleTrades` (0x5b8080): for each of the 17 commodity rows, every nation with a positive offer is paired with every nation with a negative (bid) entry for that row
  that passes two `TDiplomacyMgr` checks (vtable +0x64 and +0x44 must both be false, i.e. not an embargo / not at war), and a deal record (buyer, seller, quantity, the pair's
  relation score from the +0x79c matrix) is posted to the row's list through a method at vtable +0x38. The order of bidders in that list is the "first in line" order the manual describes;
  `TTradeMgr_GetPartnerRank` (0x5b8da0) is the ranking helper (returns -1 for a pair that may not trade). Great Powers 0-6 are paired first, then minors 7-22, rows 0-6, 7-12, 13-16 are
  walked in separate loops.
* `TTradeMgr_UpdatePrice` (0x5b8ad0) per row: Fuel (row 12) = 3 x the Oil price; Steel, Fabric, Lumber, Paper and Arms (rows 8-11, 16) are derived from their inputs' prices
  (about three times the average of the input prices, blended with a third of a finished-goods price); every other row moves with demand versus supply from last turn's
  counts, capped at 32,000. In play Hardware fell 1,204 -> 1,191 after we sold 10 and Food 72 -> 67 after we bought 6; the exact formula was not reproduced.
