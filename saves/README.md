# Test save games

Saves used to get the real game back to a known situation quickly. They are small (about 400 KB) files written by the game
itself from a freshly generated random world; they contain no game code or assets.

To use one: close the game, copy the file to `<game folder>\Save\slot0.imp`, start the game, then
Game Controls (top-bar icon) -> Load Game -> slot 0.

| File | Situation |
|---|---|
| `start_turn0.imp` ("T0 first world") | New game as Brosoptendall (power index 1), Introductory, spring 1815, nothing ordered, $50,000, briefings and warnings off. World: Brosoptendall at the top, Zimm and Loke below it |
| `t0_clean_start.imp` ("T0 clean start") | Same, in a different random world (Brosoptendall bottom right; the map in the saved-game preview has a yellow country top-left) |
| `t1_orders_queued.imp` ("T1 hardware railcars capitol") | Summer 1815, turn 1, same world as `t0_clean_start`: Hardware 1, rail cars 2 and a Capitol growth order queued, Food/Clothing/Furniture 4 each; use it to test delivery by ending the turn |
| `oil_t0.imp` ("T0 oil age ready") | Spring 1815, turn 0, local power index 2, $50,000, **Oil Drilling known for the local power** (the record the capital screen checks), Oil 20 and Fuel 20 in stock, nothing built; the Refinery and Power Plant sites are live |
| `oil_refinery4.imp` ("T3 refinery cap 4") | Same world, turn 3: Refinery built and expanded to capacity 4 (Lumber and Steel 16), Fuel 20, Power Plant not built |

Add new fixtures here with a one-line description (what turn, what orders, what stock) so tests can name them.

## Naming saves

In the game: Game Controls -> Save Game -> click a slot (its name becomes an edit box) -> End, Backspace to clear -> type -> click Save Game.
(`harness/prod_save.ps1 <file> "<slot name>"` does this.) The name is stored in the file as a 32-byte text field at offset 12, so
`python -I tools/name_save.py saves/x.imp "new name"` renames one without starting the game. Keep names to 31 characters.
