# Production recipes (read from TCity_Reset, 0x4b2570)

Each great power has ONE `TCity` (its capital and industrial centre, at nation+0x894). `TCity_Reset` creates its order
objects and stores them at city+0xe4+slot. Init call: `order.vf17(city, output, input1, input2, last)`; goods are the
trade-table rows (0 Cotton, 1 Wool, 2 Timber, 3 Coal, 4 Iron, 5 Horses, 6 Oil, 7 Food, 8 Fabric, 9 Lumber, 10 Paper,
11 Steel, 12 Fuel, 13 Clothing, 14 Furniture, 15 Hardware, 16 Arms). -1 = no second input.

| city+off | class | output | input 1 | input 2 | last arg = capacity category | confidence |
|---|---|---|---|---|---|---|
| 0x104 | TOrItemOrder | Fabric (8) | Wool (1) | Cotton (0) | 0 | likely: "either/or" input class |
| 0x108 | TItemOrder | Lumber (9) | Timber (2) | - | 4 | likely |
| 0x10c | TItemOrder | Paper (10) | Timber (2) | - | 4 | likely |
| 0x110 | TItemOrder | Steel (11) | Iron (4) | Coal (3) | 2 | likely |
| 0x114 | TItemOrder | Fuel (12) | Oil (6) | - | 6 | likely |
| 0x118 | TItemOrder | Clothing (13) | Fabric (8) | - | 1 | likely |
| 0x11c | TItemOrder | Furniture (14) | Lumber (9) | - | 5 | likely |
| 0x120 | TItemOrder | Hardware (15) | Steel (11) | - | 3 | likely |
| 0x124 | TItemOrder | Arms (16) | Steel (11) | - | 3 | likely |
| 0x100 | TFoodProcessingOrder | Food (7) | (several food stocks) | | | likely |
| 0x1b4 | TPowerPlantOrder | power | | | | guess |
| 0x140/0x144 | TTrainingOrder (1, 2) | labor training | | | | guess |
| 0x164 | TUnitOrder | military units | args 0x18,0x10,2,-1,0,5000,4,1 | | | guess |
| 0x1b0 | TCapacityOrder | factory expansion | args 0xe,9,0xb | | | guess |
| 0x1d4 | TPopGrowthOrder | population growth | | | | guess |

## The last argument is the capacity category (confirmed from the code)

`TItemOrder_vf17(city, item, in1, in2, cat)` stores `item` at +0x48, `in1`/`in2` at +0x4e/+0x50 and `cat` at +0x52.
`cat` indexes two per-nation arrays of shorts: **max capacity** at nation+0x1dc and **capacity left this turn** at
nation+0x1fc. So the seven categories are: 0 textile mill (Fabric), 1 clothing factory, 2 steel mill, 3 metal works
(Hardware and Arms share it), 4 lumber mill (Lumber and Paper share it), 5 furniture factory, 6 refinery (Fuel).

* `GetMaxAmount` = min(inputs, labor/2, capacity left); the code stored at order+0x40 says which one binds
  (0 inputs, 1 labor, 2 capacity).
* `SetAmount` subtracts the change from capacity-left (`nation+0x1fc[cat]`), and `Complete` adds the amount back, so
  capacity is a per-turn budget that refills when the order is delivered.
* `TCity_Reset` zeroes the max and shrinks capacity-left by it; `TExpansionOrder` completion sets the new max and
  adds the difference to capacity-left. Starting values written there: 2 for categories 0, 2, 4 and 1 for 1, 3, 5
  (only when game option g_Game+0x40 < 2 and the nation flag +0xa0 is set; meaning of that flag is a guess).

Consistent with the price formulas in trade_rows.txt (Fabric from Wool/Cotton, Steel from Iron/Coal, Clothing from
Fabric, Lumber and Paper from Timber, Hardware and Arms from Steel, Fuel from Oil). The last argument is probably a
UI/industry index; unconfirmed. Stock lives at city+0x1fc (23 shorts), per-turn reserved amounts at +0x1dc.

Terminology fix: earlier notes called `TCity` one of many cities; evidence says it is the single per-nation capital.
