"""Read-only: where to click the map. Picks the nearest tile a Prospector may search that the local player can SEE is unprospected
(barren hills or mountain, our own land, our prospected bit clear, no other prospector already working there) and prints it as game pixels,
or says 'scroll' when nothing eligible is on screen (then click the toolbar's "Search In" tile, game (539,315) hills / (539,335) mountains).
Usage: python -I maptarget.py prospect [x y]     x y = the prospector's tile (default: the selected unit)
Screen geometry (calibrated 2026-11-01 on fixture play_fall1817, verified by a real search order): the visible window is tiles with +0x10 != 0xff,
index 0 is its top-left tile (ox, oy); mirror pixels x = 22 + 126*(x-ox) + 63*((y&1)-(oy&1)), y = 140 + 130*(y-oy);
game pixels = ((mx - 10.4) / 1.993, (my - 34.5) / 1.993). Only player-visible data is used (terrain, owner, our own prospected bit)."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readmap as rm

g = rm.Game(); tiles, prov = g.load()
me = rm.local_nation()
MAX_LEVEL = 3        # guess: levels I-III in the manual; the real cap depends on technology (to be confirmed by trying)


def window_origin():
    for i in range(rm.N):
        if tiles[i * rm.STRIDE + 0x10] == 0:
            return i % rm.W, i // rm.W
    return None


def to_game_win(x, y, ox, oy):
    # anchored on the visible-window origin (+0x10 == 0 tile); used after a toolbar "Search In" scroll, where no unit is centred
    mx = 22 + 126 * (x - ox) + 63 * ((y & 1) - (oy & 1)); my = 140 + 130 * (y - oy)
    return mx, my, round((mx - 10.4) / 1.993), round((my - 34.5) / 1.993)


def to_game(x, y, ox, oy):
    # anchored on the SELECTED unit: Next Unit (and any order that selects a unit) scrolls the map so that unit's tile sits at mirror (589 + 63*(row odd), 530)
    mx = 589 + 126 * (x - ox) + 63 * (y & 1); my = 530 + 130 * (y - oy)
    return mx, my, round((mx - 10.4) / 1.993), round((my - 34.5) / 1.993)


def selected_tile():
    sel = struct.unpack('<I', g.rd(struct.unpack('<I', g.rd(0x6a43dc, 4))[0] + 4, 4))[0]
    return struct.unpack_from('<h', g.rd(sel, 0x28), 6)[0] if sel else None


def busy_targets():
    """tiles another civilian is working on (order 8 prospect: unit sits on the tile, so just the tiles holding units)"""
    return {i for i in range(rm.N) if struct.unpack('<I', tiles[i * rm.STRIDE + 0x20:i * rm.STRIDE + 0x24])[0]}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'prospect'
    st = selected_tile()
    o = None if st is None or st < 0 else (st % rm.W, st // rm.W)
    conv = to_game
    if len(sys.argv) > 2 and cmd == 'prospect':          # prospect <shift>: window-origin mode, shift = rows the real top row lies above the +0x10 == 0 tile (0 or 1);
        w = window_origin()                              # click candidates from a different shift if the first misses (a wrong guess hits another tile or nothing)
        o = None if w is None else (w[0], w[1] - int(sys.argv[2]))
        conv = to_game_win
    if cmd not in ('prospect', 'farmer', 'miner'):
        print(__doc__); return
    if o is None:
        print('scroll'); return
    ox, oy = o
    busy = busy_targets() - {st}          # tiles other units stand on (the selected unit's own tile is fine)
    best = None
    for i in range(rm.N):
        r = tiles[i * rm.STRIDE:(i + 1) * rm.STRIDE]
        if rm.owner_of(tiles, prov, i) != me or i in busy:
            continue
        res = {rm.sbyte(r[0x11]), rm.sbyte(r[0x12])}
        if cmd == 'prospect':
            if r[0] not in (2, 3) or r[0x13] not in (8, 9) or r[0x0d] >> me & 1:
                continue
        elif cmd == 'farmer':          # farm / plantation / orchard tiles (grain 17, fruit 18, cotton 0 visible from the terrain)
            if r[0x13] not in (2, 5, 6) or r[0x0c] & 15 >= MAX_LEVEL:    # developed level of slot 0 = low nibble of tile +0x0c (FUN_00513660)
                continue
        elif not (r[0x0d] >> me & 1 and res & {3, 4, 21, 22}) or r[0x0c] >> 4 >= MAX_LEVEL:   # miner: a prospected mineral; slot 1 level = high nibble
            continue
        x, y = i % rm.W, i // rm.W
        mx, my, gx, gy = conv(x, y, ox, oy)
        if not (60 < mx < 1000 and 120 < my < 940):
            continue
        if cmd != 'prospect' and rm.sbyte(r[0x11]) == -1 and rm.sbyte(r[0x12]) == -1 and cmd == 'miner':
            continue
        lvl = (r[0x0c] & 15) if cmd == 'farmer' else (r[0x0c] >> 4) if cmd == 'miner' else 0
        d = lvl * 100 + abs(x - ox) + abs(y - oy)          # lowest level first, then nearest the selected unit (which is in the middle of the screen)
        if best is None or d < best[0]:
            best = (d, x, y, gx, gy)
    print('scroll' if best is None else '%d %d %d %d' % best[1:])


main()
