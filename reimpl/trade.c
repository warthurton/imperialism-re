/*
 * trade.c -- the Board of Trade / Offer Sheet settlement as seen in play (fixture oil_plant_built, Winter 1817 - Summer 1817). Original code.
 *
 * Rules [confirmed in play unless stated]:
 *  - at most FOUR bids per turn (a fifth click is ignored until one is closed); sell offers have no such limit; orders are remembered between turns
 *  - you can only offer goods in the warehouse (what is not already ordered into production); an offer defaults to the whole stock
 *  - a turn's deals are settled in the commodity order of the board (Clothing, Furniture, Hardware, Arms, Food, Fabric, Lumber, Paper, Steel,
 *    Cotton, Wool, Timber, Coal, Iron, Horses) and EVERY unit sold or bought uses one unit of merchant marine ("the ship icon", 16 in the
 *    fixture); when it is used up, later offers never reach you.  Seen: sold 10 Clothing + 6 Furniture = 16 (4 Furniture stayed, 4 bids got nothing);
 *    10 Hardware sold then 3 Food offers x 2 accepted = 16, Coal/Timber/Wool offers never came
 *  - each purchase is an offer sheet: country, units, price per unit; you accept up to the offered amount; the price paid is the sheet's price
 *  - the turn's bottom line = sold - bought - military upkeep (150 here) + overseas profits; cash changes by it
 *  - a Consulate with the seller makes each trade improve relations (hot text on the sheet)
 * Build and test:  clang -O1 -Wall -o trade_test trade.c && ./trade_test
 */
#include <stdio.h>
#include <string.h>

#define MAX_BIDS 4

typedef struct Board {
    int bids[MAX_BIDS], n_bids;     /* commodity row numbers */
} Board;

int place_bid(Board *b, int row)
{
    int i;
    for (i = 0; i < b->n_bids; i++) if (b->bids[i] == row) return 1;
    if (b->n_bids >= MAX_BIDS) return 0;                         /* seen: refused */
    b->bids[b->n_bids++] = row; return 1;
}
void close_bid(Board *b, int row)
{
    int i;
    for (i = 0; i < b->n_bids; i++) if (b->bids[i] == row) { b->bids[i] = b->bids[--b->n_bids]; return; }
}

/* Merchant marine: one unit per unit moved either way. Returns the units that can actually move out of `want`. */
int ship(int *capacity_left, int want)
{
    int n = want < *capacity_left ? want : *capacity_left;
    *capacity_left -= n;
    return n;
}

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

int main(void)
{
    Board b; int cap, sold_clothing, sold_furniture, bought;
    memset(&b, 0, sizeof b);
    CHECK(place_bid(&b, 4) && place_bid(&b, 9) && place_bid(&b, 10) && place_bid(&b, 11));
    CHECK(!place_bid(&b, 12));                                   /* the fifth bid is refused (seen: Coal) */
    close_bid(&b, 9); CHECK(place_bid(&b, 12));                  /* after closing Cotton, Coal is accepted (seen) */

    cap = 16;                                                    /* Summer 1817: offered 10 Clothing and 10 Furniture */
    sold_clothing = ship(&cap, 10); sold_furniture = ship(&cap, 10);
    CHECK(sold_clothing == 10 && sold_furniture == 6 && cap == 0);   /* seen: 10 Clothing to Bruhr, 6 Furniture to Sindel */
    bought = ship(&cap, 6); CHECK(bought == 0);                  /* seen: Bought $0, the four bids got no offers */
    CHECK(10 * 1179 + 6 * 1130 - 150 == 18420);                  /* seen: Bottom Line $18,420 (cash 51,818 -> 70,238) */

    cap = 16;                                                    /* Winter 1817: 10 Hardware sold, then Food at 2 units a sheet */
    CHECK(ship(&cap, 10) == 10 && ship(&cap, 2) == 2 && ship(&cap, 2) == 2 && ship(&cap, 2) == 2 && cap == 0);
    CHECK(10 * 1191 - 6 * 67 - 150 == 11358);                    /* seen: Bottom Line $11,358 (cash 41,950 -> 53,308) */
    puts(fails ? "trade model: FAILURES" : "trade model: all checks pass");
    return fails != 0;
}
