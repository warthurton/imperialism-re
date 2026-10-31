/* Tech release schedule and prices, from Imperialism.exe (0x66ab9a windows, 0x66aaf4 prices), see docs/technology.md.
 * Build: cc -o tech tech.c && ./tech   [Cotton Gin $1,000 and Streamlined Hulls $1,500 and the release rule confirmed in play; the rest read] */
#include <stdio.h>
static const struct { int id, lo, hi, price; } TECH[26] = {
    { 3, 4, 20, 1000 }, /* Cotton Gin */
    { 4, 24, 40, 1500 }, /* Streamlined Hulls */
    { 5, 24, 40, 1500 }, /* Square-Set Timbering */
    { 6, 24, 40, 1500 }, /* Iron Railroad Bridge */
    { 7, 24, 40, 1500 }, /* Feed Grasses */
    { 8, 44, 60, 3000 }, /* Spinning Jenny */
    { 9, 44, 60, 3000 }, /* Paddlewheels */
    { 10, 64, 80, 3000 }, /* Steel Plows */
    { 11, 84, 100, 6000 }, /* Bessemer Converter */
    { 12, 84, 100, 7000 }, /* Compound Steam Engine */
    { 13, 104, 120, 10000 }, /* Rifled Artillery */
    { 14, 104, 120, 12000 }, /* Breech-Loading Rifles */
    { 15, 124, 140, 12000 }, /* Advanced Iron Working */
    { 16, 124, 140, 12000 }, /* Power Loom */
    { 17, 144, 160, 12000 }, /* Mechanical Reaper */
    { 18, 164, 180, 12000 }, /* Commercial Fertilizer */
    { 19, 164, 180, 25000 }, /* Oil Drilling */
    { 20, 184, 200, 20000 }, /* Barbed Wire */
    { 21, 204, 220, 40000 }, /* Steel Armor Plate */
    { 22, 224, 240, 40000 }, /* Large Artillery */
    { 23, 224, 240, 40000 }, /* Dynamite */
    { 24, 224, 240, 40000 }, /* Marine Engineering */
    { 25, 244, 260, 100000 }, /* Machine Guns */
    { 26, 244, 260, 120000 }, /* Chemistry */
    { 27, 264, 280, 150000 }, /* Improved Range-Finding */
    { 28, 264, 280, 150000 }, /* Internal Combustion */
};
static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

/* FUN_005af330: turn = lo + rand % (hi - lo + 1); here we only check the window. FUN_005af980: a tech is released when the turn counter equals its slot. */
static int released_at(int slot_turn, int counter) { return slot_turn == counter; }

int main(void)
{
    int i;
    for (i = 0; i < 26; i++) {
        CHECK(TECH[i].id == i + 3);
        CHECK(TECH[i].lo <= TECH[i].hi);
        CHECK(TECH[i].lo % 4 == 0 && TECH[i].hi % 4 == 0);          /* windows are whole years */
        if (i) CHECK(TECH[i].lo >= TECH[i - 1].lo);                 /* later techs never earlier */
    }
    CHECK(TECH[0].price == 1000 && TECH[1].price == 1500);          /* seen: Cotton Gin $1,000, Streamlined Hulls $1,500 */
    CHECK(TECH[0].lo == 4 && TECH[0].hi == 20 && TECH[1].lo == 24);  /* nothing but the Cotton Gin before 1821 */
    CHECK(released_at(8, 8) && !released_at(8, 7) && !released_at(8, 9));   /* seen: slot 8 released when the counter reached 8, not before */
    puts(fails ? "tech model: FAILURES" : "tech model: all checks pass");
    return fails != 0;
}
