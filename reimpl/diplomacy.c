/*
 * diplomacy.c -- a readable model of the part of Imperialism's (1997) diplomacy manager that has been decoded and checked,
 * written from the decompile (TDiplomacyMgr @ vtable 0x654d90) and from numbers read out of the running game.
 *
 * Original code reproducing behaviour, not decompiler output. Confidence marks: [confirmed] seen in the running game,
 * [code] read in the code only, [guess]. See docs/diplomacy.md for what is NOT decoded yet (how overtures are accepted,
 * where consulates and embassies are stored, why a war declaration moves other nations' scores).
 *
 * Build and self-test:  clang -O1 -Wall -o diplomacy_test diplomacy.c && ./diplomacy_test
 */
#include <stdio.h>
#include <string.h>

enum { NATIONS = 23, GREAT_POWERS = 7 };        /* nations 0-6 are the Great Powers, 7-22 the sixteen Minor Nations */

/* treaty status codes, TDiplomacyMgr_SetStatusEx switch @ 004f1b70 */
enum Status { ST_ALLIANCE = 2, ST_PACT = 3, ST_PEACE = 4, ST_EMPIRE = 5, ST_WAR = 6 };
/* 2 alliance and 6 war: [code] and 4 = the start value of every pair and 6 = war [confirmed in play]; 3 and 5 are [guess] as to meaning,
 * but the relationship effect each has is [code]. */

typedef struct Diplo {
    short relation[NATIONS][NATIONS];           /* +0x79c  score 0..255, symmetric                        [confirmed] */
    short status[NATIONS][NATIONS];             /* +0xbbe  treaty status code, symmetric                  [confirmed] */
    short turn[NATIONS][NATIONS];               /* +0xfe0  game turn the status last changed, -1 = never  [confirmed] */
} Diplo;

/* TDiplomacyMgr_GetStatus @ 004f1b10 */
int get_status(const Diplo *d, int a, int b) { return d->status[a][b]; }

/* TDiplomacyMgr_IsAtWar @ 004ef540: status 6 (and both nations exist). Seen: declaring war on Pram made G2-M11 go 4 -> 6. */
int is_at_war(const Diplo *d, int a, int b) { return get_status(d, a, b) == ST_WAR; }

/* TDiplomacyMgr_IsGreatPower @ 004f1f50 */
int is_great_power(int n) { return n < GREAT_POWERS; }

/* TDiplomacyMgr_SetRelationship @ 004efcb0  [code; the resulting numbers were seen in play]
 * Symmetric write. Negative -> 0. Above 255 -> 255 (unless a == b). Below 50 is only allowed while at war: otherwise the value is 50. */
void set_relationship(Diplo *d, int a, int b, int value)
{
    int u = value < 0 ? 0 : value;
    if (value > 0xff && a != b) u = 0xff;
    if (value < 0x32) {
        u = is_at_war(d, a, b) ? value : 0x32;
        if (u < 0) u = 0;
    }
    d->relation[a][b] = d->relation[b][a] = (short)u;
}

/* TDiplomacyMgr_SetStatusEx @ 004f1b70: the table write is [confirmed] (status and turn stamp, both halves);
 * the relationship consequence of each code is [code]. */
void set_status(Diplo *d, int a, int b, int code, int turn)
{
    d->status[a][b] = d->status[b][a] = (short)code;
    d->turn[a][b] = d->turn[b][a] = (short)turn;
    switch (code) {
    case ST_ALLIANCE:                           /* event 0x1a, then falls through into 3 and 4 as the decompile shows (unverified: the */
    case ST_PACT:                               /* switch is partly scrambled there): relation + 10 ...                              */
        set_relationship(d, a, b, d->relation[a][b] + 10);
        /* fall through */
    case ST_PEACE:                              /* ... and at least 50 */
        if (d->relation[a][b] < 0x32) set_relationship(d, a, b, 0x32);
        break;
    case ST_EMPIRE:                             /* joined the Empire: relationship maxed */
        set_relationship(d, a, b, 0xff);
        break;
    case ST_WAR:                                /* the score drop is NOT here; it comes from code not found yet (docs/diplomacy.md) */
        break;
    }
}

/* TDiplomacyMgr_CountAllies @ 004f2050 [code]: Great Powers with status 2 towards nation n. */
int count_allies(const Diplo *d, int n)
{
    int k = 0;
    for (int g = 0; g < GREAT_POWERS; g++) if (d->status[n][g] == ST_ALLIANCE) k++;
    return k;
}

/* The start of a game as read from memory (Introductory, spring 1815, turn 0) [confirmed in play]:
 * every pair has status 4 and turn -1; scores are 90 between a Great Power and anyone, 110 between two Minor Nations,
 * 150 between neighbouring Minor Nations, 110 between the human Great Power and its four starting consulate nations,
 * and 255 (minor) / 256 (great power) with itself. */
void start_of_game(Diplo *d)
{
    for (int a = 0; a < NATIONS; a++)
        for (int b = 0; b < NATIONS; b++) {
            d->status[a][b] = ST_PEACE; d->turn[a][b] = -1;
            d->relation[a][b] = (a < GREAT_POWERS || b < GREAT_POWERS) ? 90 : 110;
        }
    for (int a = 0; a < NATIONS; a++) d->relation[a][a] = a < GREAT_POWERS ? 256 : 255;
}

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

int main(void)
{
    Diplo d;
    start_of_game(&d);
    CHECK(!is_at_war(&d, 2, 11) && get_status(&d, 2, 11) == ST_PEACE && count_allies(&d, 2) == 0);

    /* below 50 is refused in peace... */
    set_relationship(&d, 2, 11, 20);
    CHECK(d.relation[2][11] == 50 && d.relation[11][2] == 50);
    set_relationship(&d, 2, 11, 90);

    /* ...but allowed at war: the declaration on Pram (M11) in the real game ended at 40, status 6, turn stamp 2 */
    set_status(&d, 2, 11, ST_WAR, 2);
    CHECK(is_at_war(&d, 2, 11) && is_at_war(&d, 11, 2));
    CHECK(d.turn[2][11] == 2 && d.turn[11][2] == 2);
    set_relationship(&d, 2, 11, 40);
    CHECK(d.relation[2][11] == 40 && d.relation[11][2] == 40);
    set_relationship(&d, 2, 11, -5);
    CHECK(d.relation[2][11] == 0);                              /* negative clamps to 0 at war */
    set_relationship(&d, 2, 11, 300);
    CHECK(d.relation[2][11] == 255);                            /* and 255 is the top */

    /* peace brings the score back up to at least 50 */
    set_relationship(&d, 2, 11, 40);
    set_status(&d, 2, 11, ST_PEACE, 3);
    CHECK(!is_at_war(&d, 2, 11) && d.relation[2][11] >= 50);

    /* alliances are counted among the Great Powers only */
    set_status(&d, 2, 4, ST_ALLIANCE, 4);
    set_status(&d, 2, 5, ST_ALLIANCE, 4);
    set_status(&d, 2, 9, ST_ALLIANCE, 4);                       /* a Minor Nation: not counted */
    CHECK(count_allies(&d, 2) == 2 && is_great_power(4) && !is_great_power(9));

    /* the Empire sets the score to the maximum */
    set_status(&d, 2, 12, ST_EMPIRE, 5);
    CHECK(d.relation[2][12] == 255);

    puts(fails ? "diplomacy model: FAILURES" : "diplomacy model: all checks pass");
    return fails != 0;
}
