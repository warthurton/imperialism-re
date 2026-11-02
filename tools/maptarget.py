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


def window_origin():
    for i in range(rm.N):
        if tiles[i * rm.STRIDE + 0x10] == 0:
            return i % rm.W, i // rm.W
    return None


def to_game(x, y, ox, oy):
    mx = 22 + 126 * (x - ox) + 63 * ((y & 1) - (oy & 1)); my = 140 + 130 * (y - oy)
    return mx, my, round((mx - 10.4) / 1.993), round((my - 34.5) / 1.993)


def selected_tile():
    sel = struct.unpack('<I', g.rd(struct.unpack('<I', g.rd(0x6a43dc, 4))[0] + 4, 4))[0]
    return struct.unpack_from('<h', g.rd(sel, 0x28), 6)[0] if sel else None


def busy_targets():
    """tiles another civilian is working on (order 8 prospect: unit sits on the tile, so just the tiles holding units)"""
    return {i for i in range(rm.N) if struct.unpack('<I', tiles[i * rm.STRIDE + 0x20:i * rm.STRIDE + 0x24])[0]}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'prospect'
    o = window_origin()
    if cmd != 'prospect':
        print(__doc__); return
    if o is None:
        print('scroll'); return
    ox, oy = o
    busy = busy_targets()
    best = None
    for i in range(rm.N):
        r = tiles[i * rm.STRIDE:(i + 1) * rm.STRIDE]
        if r[0x10] == 0xff or r[0] not in (2, 3) or r[0x13] not in (8, 9) or rm.owner_of(tiles, prov, i) != me or r[0x0d] >> me & 1 or i in busy:
            continue
        x, y = i % rm.W, i // rm.W
        mx, my, gx, gy = to_game(x, y, ox, oy)
        if not (60 < mx < 1000 and 120 < my < 940):
            continue
        d = abs(x - ox - 4) + abs(y - oy - 3)          # prefer tiles near the middle of the screen
        if best is None or d < best[0]:
            best = (d, x, y, gx, gy)
    print('scroll' if best is None else '%d %d %d %d' % best[1:])


main()
