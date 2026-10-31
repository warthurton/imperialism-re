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

/* treaty status codes. The names are the game's own strings 17361 + code [confirmed]; 4 (the start value of every pair) and 6 were also seen
 * in the matrix in play. What each code does to the relationship score is read from TDiplomacyMgr_SetStatusEx @ 004f1b70 [code]. */
enum Status {
    ST_MEMBER_OF_OUR_EMPIRE = 0,                /* "Member of our Empire" */
    ST_RULER_OF_OUR_EMPIRE = 1,                 /* "Ruler of our Empire" */
    ST_ALLIANCE = 2,                            /* "Alliance" */
    ST_PACT = 3,                                /* "Non-Aggression Pact" */
    ST_PEACE = 4,                               /* "Peace" */
    ST_EMPIRE = 5,                              /* "Member" (both in the same Empire): the score is set to 255 */
    ST_WAR = 6                                  /* "War" */
};

/* TDiplomacyMgr_RelationshipLevel @ 004f19c0 [code]: the 0-255 score as the 8-level colour code on the diplomacy screen. */
int relationship_level(int score)
{
    if (score < 0x15) return 0;
    if (score < 0x32) return 1;
    if (score < 0x50) return 2;
    if (score < 0x65) return 3;
    if (score < 0x88) return 4;
    if (score < 0xab) return 5;
    if (score < 0xce) return 6;
    return 7 + (score > 0xf0);
}

typedef struct Diplo {
    short relation[NATIONS][NATIONS];           /* +0x79c  score 0..255, symmetric                        [confirmed] */
    short status[NATIONS][NATIONS];             /* +0xbbe  treaty status code, symmetric                  [confirmed] */
    short turn[NATIONS][NATIONS];               /* +0xfe0  game turn the status last changed, -1 = never  [confirmed] */
    short presence[NATIONS][NATIONS];           /* +0x1402 0 none, 1 Trade Consulate, 2 Embassy, symmetric [confirmed in play] */
    short pending[GREAT_POWERS][NATIONS];       /* each Great Power's object at +0xb2: the overture ordered for each target, -1 = none [confirmed] */
    int   cash[GREAT_POWERS];                   /* each Great Power's money (nation+0x10) */
} Diplo;

/* Overture order ids, as written into the pending table [confirmed in play unless marked]. */
enum Overture { OV_EMPIRE = 0x12d /* guess */, OV_ALLIANCE = 0x12e, OV_PACT = 0x12f, OV_PEACE = 0x130, OV_WAR = 0x131,
                OV_CONSULATE = 0x133, OV_EMBASSY = 0x134 };
enum { COST_CONSULATE = 500, COST_EMBASSY = 5000 };

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

/* TClientGreatPower_PlaceOverture @ 004ddfc0 [confirmed]: the order is written into the pending table; a Trade Consulate ($500) and an Embassy
 * ($5,000) are paid at once, War, Pact, Peace and Alliance cost nothing. id -1 cancels and refunds. Returns 1 if the order was placed. */
int place_overture(Diplo *d, int g, int target, int id)
{
    if (id == -1) {
        if (d->pending[g][target] == OV_CONSULATE) d->cash[g] += COST_CONSULATE;
        if (d->pending[g][target] == OV_EMBASSY) d->cash[g] += COST_EMBASSY;
        d->pending[g][target] = -1;
        return 1;
    }
    if (id == OV_CONSULATE || id == OV_EMBASSY) {
        int cost = id == OV_CONSULATE ? COST_CONSULATE : COST_EMBASSY;
        if (d->cash[g] < cost) return 0;
        d->cash[g] -= cost;
    }
    d->pending[g][target] = (short)id;
    return 1;
}

/* TDiplomacyMgr_ExecuteOvertures @ 004f01e0 [confirmed in play]: at End Turn each pending order is applied and the table cleared.
 * Consulate and Embassy set the presence matrix; War calls DeclareWar (status 6) unless already at war; Pact (3) and Peace (4) go to the
 * target, which for a Minor Nation always accepts (seen: Pact 4 -> 3 with the score +10, Peace 6 -> 4 with the score raised to 50). */
void execute_overtures(Diplo *d, int g, int turn)
{
    for (int n = 0; n < NATIONS; n++) {
        int id = d->pending[g][n];
        if (id == -1) continue;
        if (id == OV_CONSULATE) d->presence[g][n] = d->presence[n][g] = 1;
        else if (id == OV_EMBASSY) d->presence[g][n] = d->presence[n][g] = 2;
        else if (id == OV_WAR) { if (!is_at_war(d, g, n)) set_status(d, g, n, ST_WAR, turn); }
        else if (id == OV_PACT) set_status(d, g, n, ST_PACT, turn);
        else if (id == OV_PEACE) set_status(d, g, n, ST_PEACE, turn);
        d->pending[g][n] = -1;
    }
}

/* TGreatPower_ExecuteAid @ 004de5e0 [code, not seen in play]: foreign aid between nations with an embassy raises the score by
 * 2 for $1,000, 4 for $3,000, 6 for $5,000 and 10 for $10,000. */
int aid_bonus(int amount)
{
    switch (amount) { case 1000: return 2; case 3000: return 4; case 5000: return 6; case 10000: return 10; default: return 0; }
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

    /* the colour code: start-of-game scores 90 / 110 / 150 / 255 fall in levels 3, 4, 5 and 8; the war scores seen in play, 40 and 50, in levels 1 and 2 */
    CHECK(relationship_level(90) == 3 && relationship_level(110) == 4 && relationship_level(150) == 5 && relationship_level(255) == 8);
    CHECK(relationship_level(40) == 1 && relationship_level(50) == 2 && relationship_level(20) == 0 && relationship_level(240) == 7);

    /* Overtures as ordered in the real game: consulate in Manx, embassy in Dedge, war on Pram (turn 1), then Pact and Peace (turn 2). */
    {
        Diplo e;
        start_of_game(&e);
        memset(e.pending, -1, sizeof e.pending);
        e.cash[2] = 50000;
        for (int a = 0; a < GREAT_POWERS; a++) for (int b = 0; b < GREAT_POWERS; b++) if (a != b) e.presence[a][b] = 2;   /* embassies between the Great Powers */
        e.presence[2][19] = e.presence[19][2] = 1;                                                                        /* a starting consulate */

        CHECK(place_overture(&e, 2, 13, OV_CONSULATE) && e.cash[2] == 49500 && e.pending[2][13] == 0x133);      /* $500 at once */
        CHECK(place_overture(&e, 2, 19, OV_EMBASSY) && e.cash[2] == 44500 && e.pending[2][19] == 0x134);       /* $5,000 at once */
        CHECK(place_overture(&e, 2, 11, OV_WAR) && e.cash[2] == 44500);                                        /* war is free */
        CHECK(place_overture(&e, 2, 13, -1) && e.cash[2] == 45000 && e.pending[2][13] == -1);                  /* cancelling refunds */
        CHECK(place_overture(&e, 2, 13, OV_CONSULATE) && e.cash[2] == 44500);
        CHECK(e.presence[2][13] == 0);                                                                         /* nothing happens before End Turn */
        execute_overtures(&e, 2, 1);
        CHECK(e.presence[2][13] == 1 && e.presence[13][2] == 1 && e.presence[2][19] == 2);
        CHECK(is_at_war(&e, 2, 11) && e.turn[2][11] == 1);
        CHECK(e.pending[2][13] == -1 && e.pending[2][19] == -1 && e.pending[2][11] == -1);                     /* the table is cleared */

        set_relationship(&e, 2, 11, 40);                                                                       /* the war score seen in play */
        e.relation[2][19] = e.relation[19][2] = 101;
        CHECK(place_overture(&e, 2, 19, OV_PACT) && place_overture(&e, 2, 11, OV_PEACE));
        execute_overtures(&e, 2, 2);
        CHECK(get_status(&e, 2, 19) == ST_PACT && e.relation[2][19] == 111 && e.turn[2][19] == 2);             /* 4 -> 3, 101 -> 111 */
        CHECK(get_status(&e, 2, 11) == ST_PEACE && e.relation[2][11] == 50 && e.turn[2][11] == 2);             /* 6 -> 4, 40 -> 50 */
        CHECK(aid_bonus(1000) == 2 && aid_bonus(3000) == 4 && aid_bonus(5000) == 6 && aid_bonus(10000) == 10 && aid_bonus(7) == 0);
    }

    puts(fails ? "diplomacy model: FAILURES" : "diplomacy model: all checks pass");
    return fails != 0;
}
