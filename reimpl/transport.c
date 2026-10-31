/*
 * transport.c -- the Transport screen (the "Transport" page of the book, screen id 2014), as seen in play. Original code.
 *
 * Each food or raw material has a slider "moved / available". The bar at the bottom right is "capacity used / capacity" (here 10 / 15),
 * and the used figure is simply the sum of the sliders. A slider setting is remembered from turn to turn. What was moved arrives in the
 * warehouse at the next turn start (manual: "available for production or trade the turn after you transport them").
 * Seen: fixture oil_plant_built, sliders Fish+Meat 1/1, Fruit 4/4, Grain 5/5, capacity 10/15, 5 workers.
 *   grain slider 5 -> 3: bar 10 -> 8; the turn after grain stock 16 -> 16 (3 in, 3 eaten), fruit 19 -> ... see docs/transport.md.
 * [confirmed in play] unless stated.   Build and test:  clang -O1 -Wall -o transport_test transport.c && ./transport_test
 */
#include <stdio.h>
#include <string.h>

enum { ROW_FISH_MEAT, ROW_FRUIT, ROW_GRAIN, NUM_ROWS };

typedef struct Transport {
    short moved[NUM_ROWS];      /* slider position (units sent)             */
    short avail[NUM_ROWS];      /* the network's output of that commodity   */
    short capacity;             /* total capacity (locomotives and ships; a Railyard car adds to it) */
} Transport;

static int used(const Transport *t) { int i, u = 0; for (i = 0; i < NUM_ROWS; i++) u += t->moved[i]; return u; }

/* A click on an arrow moves one step; the right arrow is refused at the end of the slider or when the bar is full. */
int slider_step(Transport *t, int row, int dir)
{
    int v = t->moved[row] + dir;
    if (v < 0 || v > t->avail[row]) return 0;
    if (dir > 0 && used(t) >= t->capacity) return 0;            /* [likely: the bar was never full in the tests] */
    t->moved[row] = (short)v;
    return 1;
}

/* Next turn start: what was moved is added to the food stock; the workers then eat one unit each (seen: 5 workers ate 3 Grain, 1 Fruit,
 * 1 Fish-or-Meat; 7 workers' demand bar read 4 / 2 / 1).  The split is not derived here; pass what was eaten. */
void deliver(const Transport *t, short stock[NUM_ROWS], const short eaten[NUM_ROWS])
{
    int i;
    for (i = 0; i < NUM_ROWS; i++) stock[i] += t->moved[i] - eaten[i];
}

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

int main(void)
{
    Transport t = { { 1, 4, 5 }, { 1, 4, 5 }, 15 };
    short stock[NUM_ROWS] = { 5, 16, 16 }, eaten[NUM_ROWS] = { 1, 1, 3 };     /* fish+meat 2+3, fruit 16, grain 16 at turn 5 */
    CHECK(used(&t) == 10);
    CHECK(slider_step(&t, ROW_GRAIN, -1) && slider_step(&t, ROW_GRAIN, -1) && t.moved[ROW_GRAIN] == 3 && used(&t) == 8);   /* seen: 3/5 and 8/15 */
    deliver(&t, stock, eaten);
    CHECK(stock[ROW_GRAIN] == 16 && stock[ROW_FRUIT] == 19);                  /* seen: grain 16 -> 16, fruit 16 -> 19 */
    CHECK(slider_step(&t, ROW_GRAIN, 1) && slider_step(&t, ROW_GRAIN, 1) && !slider_step(&t, ROW_GRAIN, 1));   /* 5/5 is the end */
    deliver(&t, stock, eaten);
    CHECK(stock[ROW_GRAIN] == 18 && stock[ROW_FRUIT] == 22);                  /* seen: grain 16 -> 18, fruit 19 -> 22 */
    puts(fails ? "transport model: FAILURES" : "transport model: all checks pass");
    return fails != 0;
}
