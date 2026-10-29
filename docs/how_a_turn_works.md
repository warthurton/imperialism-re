# How a turn works in Imperialism (1997), as read from the code

Everything here comes from the decompiled `Imperialism.exe` (GOG build). Each claim carries a confidence: **confirmed**
(the code does exactly this), **likely** (consistent evidence, not every detail checked) or **guess**. Names are the ones in
`names/names.tsv`; details and raw offsets are in `turn_phases.md`, `trade_rows.txt` and `recipes.md`.

## The cast

| Thing | What it is | Confidence |
|---|---|---|
| 23 nations | 7 great powers (index 0-6, `TGreatPower`/`TAutoGreatPower`/`TClientGreatPower`) and 16 minors (7-22, `TRemoteMinor`) | confirmed |
| `TSimMgr` | the turn driver: one `switch` on a phase number (`TSimMgr_AdvancePhase`) | confirmed |
| `TCity` | each great power's single capital and industrial centre, at nation+0x894: stock of 23 goods, population, 60 or so order objects | likely |
| Orders (`TItemOrder` and subclasses) | one per thing you can order: slot 7-16 are the goods recipes (slot number = output good), others are training, units, capacity, power plant, growth | likely |
| `TTradeMgr` | the market: 17 commodities x 23 nations, prices, offers and bids | confirmed |
| Ministers (`TCityInteriorMinister` and personalities) | the production-side logic per nation; subclasses (Steel, Even, Rail, ShipBuilder) look like AI personalities | likely |

Goods, in table order: 0 Cotton, 1 Wool, 2 Timber, 3 Coal, 4 Iron, 5 Horses, 6 Oil (raw); 7 Food, 8 Fabric, 9 Lumber,
10 Paper, 11 Steel, 12 Fuel (intermediate); 13 Clothing, 14 Furniture, 15 Hardware, 16 Arms (finished).

## One turn, in order

The game has four turns per year (turn/4 = year offset; guess), and the phase machine below repeats each turn.

1. **Turn start (state 0x12, likely).** For every great power: `BeginTurn` runs, which calls the production minister's
   `BeginTurn`, which calls `TCity_BeginTurn` (confirmed). That function:
   * delivers **last turn's production**: calls `Complete` on the orders (slots 0-24 plus two more groups), which adds each
     order's amount to the stock of its output good;
   * adds **arrivals** (goods bought in last turn's trade) to stock, then clears them;
   * caps every stock at 9,999;
   * updates the **production score** as `old x 0.9 + this turn's output x 10` (a moving average; use unconfirmed);
   * clears all order amounts for the new turn.
2. **Waiting for players (state 5, guess).** Humans plan; the AI runs `TSimMgr_RunNonHumanPowers` (guess), which makes the
   non-human powers choose their orders.
3. **Planning orders.** Setting an amount (`TItemOrder_SetAmount`, likely) moves the inputs and labor from stock into the
   order. Single-input recipes cost 2 inputs per unit, two-input recipes 1 + 1 (Steel), Fabric takes any mix of 2 Wool/Cotton, labor is 2 per unit (likely). `reimpl/production.c` is a runnable model of these rules. The maximum
   is the smallest of labor, capacity and inputs (`GetMaxAmount`, likely); the game records which limit binds.
4. **End of the player's turn (`RunTurnOrders` / `FundOrder`, guess).** Every slot with a pending amount is paid for.
   Production is **not instant**: the paid orders finish at the next turn start (step 1).
5. **Trade phase (state 7, likely; `TSimMgr_RunTradePhase`).**
   * Each great power prepares its bids and offers; each minor picks randomly what to sell or buy
     (`TMinor_ChooseTradeOrders`, likely): it offers raws and Food when the price is above thresholds, and bids 1-2
     finished goods (Clothing, Furniture, Hardware, Arms) when cheap.
   * `TTradeMgr_ResetTurn` clears the board; `CollectGreatPowerOrders` and `CollectMinorOrders` fill it.
   * `TTradeMgr_SettleTrades` pairs each positive offer with every allowed buyer (diplomacy checks first) and calls
     `ExecuteDeal`, which moves goods between two nations and, over a network game, syncs the result.
   * `TTradeMgr_UpdatePrice` sets the price of each commodity from supply versus demand (confirmed). Derived goods follow
     formulas: Fabric = (Clothing/3 + 3 x average(Cotton, Wool)) / 2; Lumber = (Furniture/3 + 3 x Timber) / 2;
     Paper = 3 x Timber; Steel = (Hardware/3 + 3 x average(Coal, Iron)) / 2; Fuel = 3 x Oil;
     Arms = (Hardware + 3 x Steel) / 2.
   * Supply is weighted `base^(quantity - 1)`, with a base that depends on the year (about 1.10 early, 1.01 late).
6. **Bookkeeping and reports (states 9, 10, 0x14, 0x15, 0xf, 0x11; guess).** Diplomacy follow-ups, news text,
   statistics (nation rankings are normalized to a score out of 100), then back to state 0x12 for the next turn.

## What is solid and what is not

| Solid (confirmed) | Probable (likely) | Open |
|---|---|---|
| Production timing: paid last turn, delivered at turn start | Phase numbers and their meanings in `turn_phases.md` | ~~Last argument of an order's setup call~~ = capacity category, see `recipes.md` |
| Recipes and the "slot = output good" rule | Cost per unit of orders (2 / 1+1 / labor 2) | Whether `TCity_CompleteOrders` runs before or after `BeginTurn` |
| Price formulas, supply weights, table layout | Minor-nation AI thresholds | Exact use of the production score |
| Stock cap of 9,999; arrivals added at turn start | Network synchronisation points | Combat, transport and map phases (not yet read) |

## How we know

All of this was read from the code, not observed in play. The next step for confidence is to test: set an order in a real
game, end the turn, and watch the stock change at the next turn start (see `harness/`). Nothing here has been
cross-checked against a running game yet.
