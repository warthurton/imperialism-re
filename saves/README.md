# Test save games

Saves used to get the real game back to a known situation quickly. They are small (about 400 KB) files written by the game
itself from a freshly generated random world; they contain no game code or assets.

To use one: close the game, copy the file to `<game folder>\Save\slot0.imp`, start the game, then
Game Controls (top-bar icon) -> Load Game -> slot 0.

| File | Situation |
|---|---|
| `start_turn0.imp` | New game as Brosoptendall (power index 1), Introductory, spring 1815, nothing ordered, $50,000, briefings and warnings off |

Add new fixtures here with a one-line description (what turn, what orders, what stock) so tests can name them.
