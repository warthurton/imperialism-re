/*
 * production.c -- a readable model of Imperialism's (1997) production orders, written from the decompile.
 *
 * This is original code that reproduces the *behaviour* read from Imperialism.exe; it is not decompiler output.
 * Comments say where each rule comes from (function name @ address in the GOG build) and how sure we are:
 *   [confirmed] the code does exactly this    [likely] consistent evidence, not every path checked
 * Offsets (+0x..) are into the original objects, so you can look the rule up in the named decompile.
 *
 * Build and self-test:  clang -O1 -Wall -o production_test production.c && ./production_test
 */
#include <stdio.h>
#include <string.h>

/* ---- goods and capacity categories (docs/recipes.md, docs/trade_rows.txt) ---- */
enum Good {
    COTTON, WOOL, TIMBER, COAL, IRON, HORSES, OIL,               /* raw */
    FOOD, FABRIC, LUMBER, PAPER, STEEL, FUEL,                    /* intermediate */
    CLOTHING, FURNITURE, HARDWARE, ARMS,                         /* finished */
    NUM_GOODS = 17,
    NUM_STOCK = 23                                               /* the stock table has 23 shorts; 17 are goods */
};
enum Category { TEXTILE, CLOTHING_FACTORY, STEEL_MILL, METAL_WORKS, LUMBER_MILL, FURNITURE_FACTORY, REFINERY, NUM_CATS = 7 };

/* ---- the nation's capital city: the only thing orders touch ---- */
typedef struct City {
    short stock[NUM_STOCK];     /* goods on hand                          city+0xb6   [confirmed] */
    short arrivals[NUM_STOCK];  /* goods bought last turn, delivered now  city+0x2a6  [confirmed] */
    short cap_max[NUM_CATS];    /* capacity per category                  city+0x1dc  [confirmed] */
    short cap_left[NUM_CATS];   /* capacity unspent this turn             city+0x1fc  [confirmed] */
    short labor;                /* labor units available                  labor+0x1c  [confirmed in play] */
    short labor_total;          /* labor the nation has; labor is refilled to this each turn  [likely] */
    int   score;                /* production score                       city+0x78   [confirmed] */
    int   turn;                 /*                                        city+0xc */
    int   cash;                 /* the owner's money                      owner+0x10  [confirmed in play] */
    short refinery_pending;     /* a Refinery has been paid for and appears at the next turn start   [confirmed in play] */
    short plant_pending;        /* same for the Power Plant                                          [confirmed in play] */
    short workers[3];           /* untrained, trained, expert workers  [confirmed in play: left bar of the Industry screen] */
    short units_pending[4];     /* civilians paid for, reported at the next turn start (Miner, Prospector, Farmer, Engineer)  [confirmed in play] */
    short ships_pending[4];     /* ships paid for (Trader, Indiaman, Frigate, Ship-of-the-Line); appear next turn  [confirmed in play] */
    short merchant;             /* merchant marine capacity (units that can be sold or bought per turn)  [confirmed in play: 16 -> 20 for 2 Traders] */
    short refinery_expand_pending; /* an expansion (+2 capacity) has been paid for; completes at the next turn start  [confirmed in play] */
} City;

/* ---- an order that turns inputs into one output good ---- */
typedef enum { SINGLE, PAIR, EITHER } Kind;
typedef struct Order {
    Kind  kind;
    short item;                 /* output good                    order+0x48 */
    short in1, in2;             /* input goods (in2 = -1: none)   order+0x4e / +0x50 */
    short cat;                  /* capacity category              order+0x52 */
    short amount;               /* units ordered                  order+0x04 */
    short remembered;           /* last amount the player set; re-applied every turn   order+0x4c  [confirmed in play] */
    short reserved[NUM_STOCK];  /* inputs already taken from stock order+0x10 */
    short binding;              /* which limit binds: 0 inputs, 1 labor, 2 capacity   order+0x40 */
    int   produced_total;       /*                                order+0x44 */
    City *city;
} Order;

static int min2(int a, int b) { return a < b ? a : b; }

/* TItemOrder_GetMaxAmount @ 004b5310, TOrItemOrder_vf12 @ 004b58f0   [likely]
 * Every unit costs 2 labor and 2 input items. The ceiling is the smallest of the three limits, each counted
 * together with what this order already holds, so raising and lowering an order are symmetric. */
int order_max_amount(Order *o)
{
    City *c = o->city;
    int by_labor    = c->labor / 2 + o->amount;
    int by_capacity = c->cap_left[o->cat] + o->amount;
    int have1 = o->reserved[o->in1] + c->stock[o->in1];
    int by_inputs;
    if (o->kind == SINGLE) {
        by_inputs = have1 / 2;                                   /* 2 of the one input per unit */
    } else if (o->kind == PAIR) {
        int have2 = o->reserved[o->in2] + c->stock[o->in2];
        by_inputs = min2(have1, have2);                          /* 1 of each per unit */
    } else {
        int have2 = o->reserved[o->in2] + c->stock[o->in2];
        by_inputs = (have1 + have2) / 2;                         /* any mix, 2 items per unit */
    }
    o->binding = 2; int max = by_capacity;
    if (by_labor < max)  { o->binding = 1; max = by_labor; }
    if (by_inputs < max) { o->binding = 0; max = by_inputs; }
    return max;
}

/* Move n input items between stock and the order's reserve (negative n gives them back). */
static void take(Order *o, int good, int n) { o->city->stock[good] -= n; o->reserved[good] += n; }

/* TItemOrder_SetAmount @ 004b53d0, TOrItemOrder_vf11 @ 004b5990   [likely]
 * Changes the order to `amount` units; refuses (returns 0) outside 0..max. Inputs, labor and capacity are
 * charged at once and refunded if the order is lowered. */
int order_set_amount(Order *o, int amount)
{
    City *c = o->city;
    int delta = amount - o->amount;
    if (amount < 0 || amount > order_max_amount(o)) return 0;
    o->amount = (short)amount;
    o->remembered = (short)amount;
    if (o->kind == SINGLE) {
        take(o, o->in1, 2 * delta);
    } else if (o->kind == PAIR) {
        take(o, o->in1, delta);
        take(o, o->in2, delta);
    } else {
        /* Prefer 1+1; if one input runs short, the other covers the rest. When refunding, return what was
         * reserved, again preferring an even split. */
        int a = delta < 0 ? -delta : delta;
        int s1 = delta < 0 ? o->reserved[o->in1] : c->stock[o->in1];
        int s2 = delta < 0 ? o->reserved[o->in2] : c->stock[o->in2];
        int n1 = a, n2 = a;
        if (s1 < a)      { n1 = s1; n2 = a + (a - s1); }
        else if (s2 < a) { n2 = s2; n1 = a + (a - s2); }
        if (delta < 0)   { n1 = -n1; n2 = -n2; }
        take(o, o->in1, n1);
        take(o, o->in2, n2);
    }
    c->labor        -= 2 * delta;
    c->cap_left[o->cat] -= delta;
    return 1;
}

/* TItemOrder_Complete @ 004b5580   [confirmed]
 * Delivery: the output joins stock, capacity comes back, inputs held by the order are consumed. */
void order_complete(Order *o)
{
    City *c = o->city;
    c->stock[o->item]   += o->amount;
    c->cap_left[o->cat] += o->amount;
    c->score            += o->amount;      /* city+0x78 running total, folded into the score by begin_turn */
    o->produced_total   += o->amount;
    memset(o->reserved, 0, sizeof o->reserved);
}

/* TItemOrder_ResetAmount @ 004b5620   [confirmed in play: the order is charged again each turn]
 * After delivery the order is emptied and the remembered amount is re-applied, so a standing order repeats every
 * turn until the player changes it. If inputs (not labor or capacity) fall short, the largest affordable amount is
 * taken but the remembered figure is kept for later turns. */
void order_reset_amount(Order *o)
{
    int max = order_max_amount(o);
    short r = o->remembered;
    int inputs_bind = (o->binding == 0);
    o->amount = 0;
    if (max < r && inputs_bind) { order_set_amount(o, max); o->remembered = r; }
    else                        order_set_amount(o, r);
}

/* ---- Power Plant (TPowerPlantOrder, city+0x1b4): turns Fuel into labor ---- [confirmed in play, docs/production_playtest.md]
 * One unit of fuel gives 6 units of power (TPowerPlantOrder_vf16 @ 004b7c90: power = amount * 6); power is added straight to the
 * available labor (labor obj +0x1c) and is not a commodity. The order's amount is in POWER units; its maximum is the current amount plus the Fuel in
 * stock x 6 (TPowerPlantOrder_vf12 @ 004b7b00). The help text's "up to 100 units of fuel per turn" is NOT enforced: with 150 Fuel the slider took all 150 (900 power).
 * Like every other order it is charged the moment the slider moves and is re-applied every turn from the remembered amount. */
enum { POWER_PER_FUEL = 6, PLANT_COST = 5000, REFINERY_CAPACITY = 2, REFINERY_EXPANSION = 2 };
typedef struct PowerPlant {
    short built;                /* 0 until the turn after construction                        */
    short fuel;                 /* fuel burned this turn (the slider)                         */
    short remembered;           /* last amount set; re-applied at every turn start            */
    City *city;
} PowerPlant;

int power_set_fuel(PowerPlant *pp, int fuel)
{
    City *c = pp->city;
    int delta = fuel - pp->fuel;
    if (!pp->built || fuel < 0) return 0;
    if (delta > c->stock[FUEL]) return 0;                       /* not enough fuel in stock: refused */
    c->stock[FUEL] -= delta;                                    /* seen: Fuel 20 -> 19 */
    c->labor += delta * POWER_PER_FUEL;                         /* seen: labor 16 -> 22 */
    pp->fuel = pp->remembered = (short)fuel;
    return 1;
}

/* ---- constructing the two oil-age buildings (capital screen building sites; TBuildingConstructionView) ---- [confirmed in play]
 * Available only when the local power's tech record for Oil Drilling is 2 (TCityProductionView_vf53/vf71).
 * Refinery: capacity 2 from the start, 1 Lumber + 1 Steel per capacity point taken at once; the capacity appears at the next
 * turn start. Clicking the site again while it is pending offers "Cancel construction" and refunds the materials.
 * Power Plant: $5,000 at once, built at the next turn start (cancelling it was not tried). */
int build_refinery(City *c)
{
    if (c->cap_max[REFINERY] || c->refinery_pending) return 0;
    if (c->stock[LUMBER] < REFINERY_CAPACITY || c->stock[STEEL] < REFINERY_CAPACITY) return 0;
    c->stock[LUMBER] -= REFINERY_CAPACITY; c->stock[STEEL] -= REFINERY_CAPACITY;
    c->refinery_pending = 1;
    return 1;
}
int cancel_refinery(City *c)
{
    if (!c->refinery_pending) return 0;
    c->stock[LUMBER] += REFINERY_CAPACITY; c->stock[STEEL] += REFINERY_CAPACITY;   /* seen: 18/18 -> 20/20 */
    c->refinery_pending = 0;
    return 1;
}
/* Expanding the Refinery (the factory-arrow button in its production dialog -> "Expand Factory", capacity 2 -> 4): same price as
 * building, 1 Lumber + 1 Steel per point, so 2 + 2 for the +2 seen; taken at once, capacity arrives at the next turn start.
 * Pressing Cancel in the re-offered dialog while it is pending cancels the expansion and refunds it. [confirmed in play] */
int expand_refinery(City *c)
{
    if (!c->cap_max[REFINERY] || c->refinery_expand_pending) return 0;
    if (c->stock[LUMBER] < REFINERY_EXPANSION || c->stock[STEEL] < REFINERY_EXPANSION) return 0;
    c->stock[LUMBER] -= REFINERY_EXPANSION; c->stock[STEEL] -= REFINERY_EXPANSION;   /* seen: 18/18 -> 16/16 */
    c->refinery_expand_pending = 1;
    return 1;
}
int cancel_refinery_expansion(City *c)
{
    if (!c->refinery_expand_pending) return 0;
    c->stock[LUMBER] += REFINERY_EXPANSION; c->stock[STEEL] += REFINERY_EXPANSION;   /* seen: back to 18/18 */
    c->refinery_expand_pending = 0;
    return 1;
}
/* Cancelling a Power Plant that is still under construction refunds the $5,000 (seen: $45,000 -> $50,000). [confirmed in play] */
int cancel_power_plant(City *c)
{
    if (!c->plant_pending) return 0;
    c->cash += PLANT_COST; c->plant_pending = 0;
    return 1;
}
int build_power_plant(City *c, PowerPlant *pp)
{
    if (pp->built || c->plant_pending || c->cash < PLANT_COST) return 0;
    c->cash -= PLANT_COST;                                      /* seen: $50,000 -> $45,000 */
    c->plant_pending = 1;
    return 1;
}

/* TCity_BeginTurn @ 004b3b40   [confirmed]
 * 1. arrivals (last turn's purchases) join stock, then clear
 * 2. every recipe order is completed (last turn's paid production arrives)
 * 3. score = old*9/10 + (this turn's total)*10
 * 4. stock is capped at 9,999
 * 5. labor is refilled and every order is re-charged with its remembered amount (observed in play: a Lumber order of 1
 *    set once is still 1, with its 2 Timber taken again, at the start of every following turn)
 * Also: paid-for buildings are completed at the turn start, and the Power Plant re-applies its remembered fuel after the refill. */
void city_begin_turn(City *c, Order *orders, int n_orders, PowerPlant *pp)
{
    int i, old_score = c->score;
    c->turn++;
    for (i = 0; i < NUM_STOCK; i++) { c->stock[i] += c->arrivals[i]; c->arrivals[i] = 0; }
    c->score = 0;
    for (i = 0; i < n_orders; i++) order_complete(&orders[i]);
    c->score = old_score * 9 / 10 + c->score * 10;
    for (i = 0; i < NUM_STOCK; i++) if (c->stock[i] > 9999) c->stock[i] = 9999;
    if (c->refinery_pending) {                                  /* construction finishes: capacity appears (seen 0 -> 2) */
        c->cap_max[REFINERY] = c->cap_left[REFINERY] = REFINERY_CAPACITY; c->refinery_pending = 0;
    }
    if (c->plant_pending && pp) { pp->built = 1; c->plant_pending = 0; }
    if (c->refinery_expand_pending) {                           /* seen: capacity 2 -> 4 at the turn start after paying */
        c->cap_max[REFINERY] += REFINERY_EXPANSION; c->cap_left[REFINERY] += REFINERY_EXPANSION; c->refinery_expand_pending = 0;
    }
    c->labor = c->labor_total;
    for (i = 0; i < n_orders; i++) order_reset_amount(&orders[i]);
    if (pp && pp->built) {                                      /* seen: Fuel 19 -> 18 and labor 16 + 6 again with no input */
        int want = pp->remembered;                              /* if fuel runs short the remembered figure is kept */
        pp->fuel = 0;
        if (want > c->stock[FUEL]) want = c->stock[FUEL];
        { short keep = pp->remembered; power_set_fuel(pp, want); pp->remembered = keep; }
    }
}

/* ---- the nine goods recipes, as set up in TCity_Reset @ 004b2570 (docs/recipes.md)   [likely] ---- */
static void make_recipes(City *c, Order out[9])
{
    static const struct { Kind k; short item, in1, in2, cat; } R[9] = {
        { EITHER, FABRIC,    WOOL,  COTTON, TEXTILE },
        { SINGLE, LUMBER,    TIMBER, -1,    LUMBER_MILL },
        { SINGLE, PAPER,     TIMBER, -1,    LUMBER_MILL },
        { PAIR,   STEEL,     IRON,  COAL,   STEEL_MILL },
        { SINGLE, FUEL,      OIL,   -1,     REFINERY },
        { SINGLE, CLOTHING,  FABRIC, -1,    CLOTHING_FACTORY },
        { SINGLE, FURNITURE, LUMBER, -1,    FURNITURE_FACTORY },
        { SINGLE, HARDWARE,  STEEL, -1,     METAL_WORKS },
        { SINGLE, ARMS,      STEEL, -1,     METAL_WORKS },
    };
    for (int i = 0; i < 9; i++) {
        memset(&out[i], 0, sizeof out[i]);
        out[i].kind = R[i].k; out[i].item = R[i].item; out[i].in1 = R[i].in1; out[i].in2 = R[i].in2;
        out[i].cat = R[i].cat; out[i].city = c;
    }
}

/* ---- self-test: the rules above, exercised end to end ---- */
/* ---- University (civilians) and Trade School (training); seen in play, docs/production_playtest.md ----
 * Every civilian costs 1 expert worker + 2 Paper + cash, charged the moment the arrow is clicked; the expert's 4 labor go with him
 * (labor 16 -> 12 for one Miner). They are reported ("New units are reporting for duty") at the next turn start and are not re-ordered.
 * A shortage of any of the three refuses the click and charges nothing. [confirmed in play] */
enum Civilian { MINER, PROSPECTOR, FARMER, ENGINEER };
static const int CIVILIAN_CASH[4] = { 1500, 500, 1000, 2000 };
#define EXPERT_LABOR 4
int order_civilian(City *c, int kind)
{
    if (c->workers[2] < 1 || c->stock[PAPER] < 2 || c->cash < CIVILIAN_CASH[kind]) return 0;
    c->workers[2]--; c->stock[PAPER] -= 2; c->cash -= CIVILIAN_CASH[kind]; c->labor -= EXPERT_LABOR; c->labor_total -= EXPERT_LABOR;
    c->units_pending[kind]++;
    return 1;
}
/* Trade School: untrained -> trained costs 1 labor, 1 Paper, $100; trained -> expert 2 labor, 2 Paper, $1,000.  [confirmed in play] */
int train_worker(City *c, int to_expert)
{
    int grade = to_expert ? 1 : 0, n = to_expert ? 2 : 1, cash = to_expert ? 1000 : 100;
    if (c->workers[grade] < 1 || c->labor < n || c->stock[PAPER] < n || c->cash < cash) return 0;
    c->workers[grade]--; c->workers[grade + 1]++; c->labor -= n; c->stock[PAPER] -= n; c->cash -= cash;
    return 1;
}

/* ---- Shipyard: each ship costs goods only (no labor, no cash, no worker), charged when the arrow is clicked (read from the dialog, then 2 Traders
 * seen: Fabric 20 -> 16, Lumber 16 -> 8). Traders and Indiamen are merchant ships: "Our merchant capacity has increased to 20" at the next turn start,
 * +2 per Trader (Cargo 2), +4 per Indiaman (Cargo 4, read); warships carry no cargo.  [confirmed in play for the Trader; costs of the others read] */
enum Ship { TRADER, INDIAMAN, FRIGATE, SHIP_OF_THE_LINE };
static const struct { short fabric, lumber, arms, cargo; } SHIP[4] = { { 2, 4, 0, 2 }, { 3, 7, 0, 4 }, { 2, 5, 2, 0 }, { 3, 8, 5, 0 } };
int order_ship(City *c, int kind)
{
    if (c->stock[FABRIC] < SHIP[kind].fabric || c->stock[LUMBER] < SHIP[kind].lumber || c->stock[ARMS] < SHIP[kind].arms) return 0;
    c->stock[FABRIC] -= SHIP[kind].fabric; c->stock[LUMBER] -= SHIP[kind].lumber; c->stock[ARMS] -= SHIP[kind].arms;
    c->ships_pending[kind]++; return 1;
}
void complete_ships(City *c)
{
    int k;
    for (k = 0; k < 4; k++) { c->merchant += c->ships_pending[k] * SHIP[k].cargo; c->ships_pending[k] = 0; }
}

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

int main(void)
{
    City c; Order o[9];
    memset(&c, 0, sizeof c);
    make_recipes(&c, o);
    Order *steel = &o[3], *fabric = &o[0], *clothing = &o[5];

    /* Steel = 1 Iron + 1 Coal per unit; limited by the scarcer input. */
    c.stock[IRON] = 10; c.stock[COAL] = 6; c.labor = c.labor_total = 100; c.cap_left[STEEL_MILL] = 8;
    CHECK(order_max_amount(steel) == 6 && steel->binding == 0);
    CHECK(order_set_amount(steel, 7) == 0);                     /* over the max is refused */
    CHECK(order_set_amount(steel, 5) == 1);
    CHECK(c.stock[IRON] == 5 && c.stock[COAL] == 1 && c.labor == 90 && c.cap_left[STEEL_MILL] == 3);
    CHECK(order_set_amount(steel, 2) == 1);                     /* lowering refunds everything */
    CHECK(c.stock[IRON] == 8 && c.stock[COAL] == 4 && c.labor == 96 && c.cap_left[STEEL_MILL] == 6);

    /* Fabric takes any 2 of Wool/Cotton per unit, preferring 1+1; wool short -> cotton covers it. */
    c.stock[WOOL] = 1; c.stock[COTTON] = 10; c.cap_left[TEXTILE] = 9;
    CHECK(order_max_amount(fabric) == 5);
    CHECK(order_set_amount(fabric, 3) == 1);
    CHECK(c.stock[WOOL] == 0 && c.stock[COTTON] == 5);          /* 1 wool + 5 cotton = 6 items = 3 units */

    /* Single-input recipe costs 2 per unit. */
    c.stock[FABRIC] = 9; c.cap_left[CLOTHING_FACTORY] = 9;
    CHECK(order_max_amount(clothing) == 4);

    /* Production is delivered at the next turn start; capacity returns; inputs are consumed; stock capped; then the
     * standing orders are charged again from the new stock (Steel 2 remembered, Fabric 3 remembered). */
    c.stock[STEEL] = 9998; c.arrivals[COAL] = 3; c.score = 100;
    city_begin_turn(&c, o, 9, NULL);
    CHECK(c.stock[STEEL] == 9999);                              /* 9998 + 2 capped */
    CHECK(c.stock[FABRIC] == 9 + 3);                            /* 3 fabric delivered */
    CHECK(c.score == 100 * 9 / 10 + (2 + 3) * 10);
    CHECK(steel->amount == 2 && steel->remembered == 2);        /* standing order repeats */
    CHECK(c.stock[IRON] == 6 && c.stock[COAL] == 5);            /* 8-2 and (4+3 arrivals)-2 */
    CHECK(c.labor == 100 - 2 * (2 + 2) && c.cap_left[STEEL_MILL] == 6);   /* labor refilled, then 2+2 units charged */
    CHECK(fabric->amount == 2 && fabric->remembered == 3);      /* only 5 cotton left = 2 units affordable; 3 kept */
    CHECK(c.stock[COTTON] == 1 && c.stock[WOOL] == 0);

    /* ---- Refinery and Power Plant, with the numbers seen in the real game (docs/production_playtest.md) ---- */
    {
        City d; Order r[9]; PowerPlant pp;
        memset(&d, 0, sizeof d); memset(&pp, 0, sizeof pp);
        make_recipes(&d, r); pp.city = &d;
        d.stock[LUMBER] = 20; d.stock[STEEL] = 20; d.stock[OIL] = 20; d.stock[FUEL] = 20; d.cash = 50000;
        d.labor = d.labor_total = 16;
        Order *fuel = &r[4];

        CHECK(build_refinery(&d) && d.stock[LUMBER] == 18 && d.stock[STEEL] == 18);   /* materials taken at once */
        CHECK(d.cap_max[REFINERY] == 0);                        /* ...but no capacity until the next turn */
        CHECK(!build_refinery(&d));                             /* already pending */
        CHECK(cancel_refinery(&d) && d.stock[LUMBER] == 20 && d.stock[STEEL] == 20);  /* cancel refunds */
        CHECK(build_refinery(&d));
        CHECK(build_power_plant(&d, &pp) && d.cash == 45000 && !pp.built);
        CHECK(!power_set_fuel(&pp, 1));                         /* not usable before it is built */

        city_begin_turn(&d, r, 9, &pp);                         /* turn start: both buildings appear */
        CHECK(d.cap_max[REFINERY] == 2 && d.cap_left[REFINERY] == 2 && pp.built);

        /* Refinery order: per unit 2 Oil + 2 labor + 1 capacity; capacity 2 caps it (the third click was refused in play). */
        d.labor = 16;
        CHECK(order_set_amount(fuel, 1) == 1);
        CHECK(d.stock[OIL] == 18 && d.labor == 14 && d.cap_left[REFINERY] == 1);
        CHECK(order_set_amount(fuel, 2) == 1);
        CHECK(d.stock[OIL] == 16 && d.labor == 12 && d.cap_left[REFINERY] == 0);
        CHECK(order_set_amount(fuel, 3) == 0 && fuel->amount == 2 && fuel->binding == 2);

        /* Power Plant: 1 fuel -> 6 power, charged at once. */
        d.labor = 16; d.stock[FUEL] = 20;
        CHECK(power_set_fuel(&pp, 1) && d.stock[FUEL] == 19 && d.labor == 22);
        CHECK(!power_set_fuel(&pp, 400));                       /* more than the Fuel in stock is refused */

        /* Next turn start with no input: the Refinery delivers its 2 Fuel, orders are re-charged, labor refilled to 16 then +6. */
        d.labor_total = 16;
        city_begin_turn(&d, r, 9, &pp);
        CHECK(d.stock[FUEL] == 19 + 2 - 1);                     /* +2 delivered, -1 burned again */
        CHECK(d.stock[OIL] == 12 && d.cap_left[REFINERY] == 0); /* 16 - 4 re-charged */
        CHECK(d.labor == 16 - 4 + 6);                           /* refill, refinery order 2 units x 2 labor, plant +6 */
        CHECK(d.score == 2 * 10);                               /* score 20 seen in play */

        /* Expanding the Refinery and cancelling things (all seen in play). */
        d.stock[LUMBER] = 18; d.stock[STEEL] = 18; d.cash = 50000;
        CHECK(expand_refinery(&d) && d.stock[LUMBER] == 16 && d.stock[STEEL] == 16 && d.cap_max[REFINERY] == 2);
        CHECK(!expand_refinery(&d));                            /* already pending */
        CHECK(cancel_refinery_expansion(&d) && d.stock[LUMBER] == 18 && d.stock[STEEL] == 18);
        CHECK(expand_refinery(&d));
        city_begin_turn(&d, r, 9, &pp);
        CHECK(d.cap_max[REFINERY] == 4);                        /* seen: 2 -> 4 after the turn */
        {
            City e; PowerPlant q; memset(&e, 0, sizeof e); memset(&q, 0, sizeof q); q.city = &e; e.cash = 50000;
            CHECK(build_power_plant(&e, &q) && e.cash == 45000);
            CHECK(cancel_power_plant(&e) && e.cash == 50000 && !e.plant_pending);
        }
    }

    /* Power Plant limits, seen in play (fixture oil_plant_built, 150 Fuel): no cap at 100, and a standing order survives running out of Fuel. */
    {
        City d; PowerPlant pp;
        memset(&d, 0, sizeof d); memset(&pp, 0, sizeof pp);
        pp.city = &d; pp.built = 1; d.labor = d.labor_total = 16; d.stock[FUEL] = 150;
        CHECK(power_set_fuel(&pp, 150) && d.stock[FUEL] == 0 && d.labor == 16 + 900);   /* all 150 Fuel = 900 power (seen), not 100 */
        CHECK(!power_set_fuel(&pp, 151));                                              /* but never more than the stock */
        city_begin_turn(&d, NULL, 0, &pp);                      /* the next turn starts with 0 Fuel: no power, labor back to 16 (seen) */
        CHECK(pp.fuel == 0 && d.labor == 16 && pp.remembered == 150);
        d.stock[FUEL] = 30;
        city_begin_turn(&d, NULL, 0, &pp);                      /* 30 Fuel: all burned, 180 power (seen); the 150 order is still remembered */
        CHECK(pp.fuel == 30 && d.stock[FUEL] == 0 && d.labor == 16 + 180 && pp.remembered == 150);
    }

    /* University and Trade School, seen in play (fixture oil_plant_built: 2 experts, 20 Paper, $44,400, labor 16). */
    {
        City u; memset(&u, 0, sizeof u);
        u.workers[2] = 2; u.stock[PAPER] = 20; u.cash = 44400; u.labor = u.labor_total = 16;
        CHECK(order_civilian(&u, MINER) && u.stock[PAPER] == 18 && u.cash == 42900 && u.workers[2] == 1 && u.labor == 12);
        CHECK(order_civilian(&u, PROSPECTOR) && u.stock[PAPER] == 16 && u.cash == 42400 && u.workers[2] == 0 && u.labor == 8);
        CHECK(!order_civilian(&u, ENGINEER) && u.stock[PAPER] == 16 && u.cash == 42400);      /* no expert left: refused, nothing charged */
        CHECK(u.units_pending[MINER] == 1 && u.units_pending[PROSPECTOR] == 1);
        u.workers[0] = 2; u.workers[1] = 3; u.labor = 16; u.stock[PAPER] = 20; u.cash = 50000;
        CHECK(train_worker(&u, 0) && u.stock[PAPER] == 19 && u.cash == 49900 && u.labor == 15 && u.workers[1] == 4);
        CHECK(train_worker(&u, 1) && u.stock[PAPER] == 17 && u.cash == 48900 && u.labor == 13 && u.workers[2] == 1);
    }

    /* Shipyard, seen in play: two Traders. */
    {
        City y; memset(&y, 0, sizeof y);
        y.stock[FABRIC] = 20; y.stock[LUMBER] = 16; y.stock[ARMS] = 10; y.merchant = 16;
        CHECK(order_ship(&y, TRADER) && order_ship(&y, TRADER) && y.stock[FABRIC] == 16 && y.stock[LUMBER] == 8);
        complete_ships(&y); CHECK(y.merchant == 20);              /* seen: "merchant capacity has increased to 20" */
        CHECK(order_ship(&y, SHIP_OF_THE_LINE) && y.stock[ARMS] == 5 && y.stock[LUMBER] == 0);
        CHECK(!order_ship(&y, SHIP_OF_THE_LINE));                 /* no Lumber left: refused */
    }

    puts(fails ? "production model: FAILURES" : "production model: all checks pass");
    return fails != 0;
}
