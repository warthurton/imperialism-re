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
    if cmd == 'tile':      # tile X Y -> game pixels of that tile, anchored on the selected unit (any tile, no eligibility test)
        tx, ty = int(sys.argv[2]), int(sys.argv[3])
        if o is None:
            print('scroll'); return
        mx, my, gx, gy = to_game(tx, ty, o[0], o[1]); print('%d %d %d %d' % (tx, ty, gx, gy)); return
    if cmd == 'engineer':   # 'here' if the selected Engineer stands on a tile worth a depot, else game pixels of the nearest such tile, else 'none'
        def worth(i):        # own land, nobody gathers it yet (+0x05 = 255), no structure, and it carries something to gather (visible farm kinds or a prospected mineral)
            r = tiles[i * rm.STRIDE:(i + 1) * rm.STRIDE]
            if r[0x05] != 255 or r[0x1c] or rm.owner_of(tiles, prov, i) != me or r[0] == 5:
                return False
            res = {rm.sbyte(r[0x11]), rm.sbyte(r[0x12])}
            return r[0x13] in (2, 5, 6) or bool(r[0x0d] >> me & 1 and res & {3, 4, 21, 22})
        if o is None:
            print('none'); return
        if worth(st):
            print('here'); return
        best = None
        for i in range(rm.N):
            if worth(i) and i not in busy_targets():
                x, y = i % rm.W, i // rm.W
                d = abs(x - o[0]) + abs(y - o[1])
                if best is None or d < best[0]:
                    best = (d, x, y)
        if best is None:
            print('none'); return
        mx, my, gx, gy = to_game(best[1], best[2], o[0], o[1])
        print('%d %d %d %d' % (best[1], best[2], gx, gy) if 60 < mx < 1000 and 120 < my < 940 else 'scroll'); return
    if cmd == 'rail':
        # Connect an unconnected depot to the rail network with the selected Engineer. Output: "lay GX GY" (the Engineer stands at one end of the next missing
        # piece: click the other end), "move GX GY" (deploy him to that end first), or "none". Uses only what the player sees: our own rail (+0x17), our land, terrain.
        if o is None:
            print('none'); return
        W = rm.W
        def rail(i):
            return tiles[i * rm.STRIDE + 0x17]
        def nbrs(i):
            return [(b, rm.linked_tile(i, b)) for b in range(6) if 0 <= rm.linked_tile(i, b)[0] < W and 0 <= rm.linked_tile(i, b)[1] < rm.H]
        def idx(t):
            return t[1] * W + t[0]
        def can(i):           # early rail: plains, forest, farmland on our own land (hills, mountains, swamp need technology)
            r = tiles[i * rm.STRIDE:(i + 1) * rm.STRIDE]
            return r[0] in (0, 1, 7) and rm.owner_of(tiles, prov, i) == me
        capital = [i for i in range(rm.N) if tiles[i * rm.STRIDE + 0x1c] & 0x08 and rm.owner_of(tiles, prov, i) == me]
        if not capital:
            print('none'); return
        # tiles already tied to the capital by rail
        net = set(capital); stack = list(capital)
        while stack:
            i = stack.pop()
            for b, t in nbrs(i):
                j = idx(t)
                if rail(i) >> b & 1 and j not in net:
                    net.add(j); stack.append(j)
        depots = [i for i in range(rm.N) if tiles[i * rm.STRIDE + 0x1c] & 0x10 and rm.owner_of(tiles, prov, i) == me and i not in net]
        occupied = busy_targets() - {o[1] * W + o[0]}
        best = None
        for d in depots:
            # breadth-first search from the depot over tiles rail can cross, to the nearest tile of the network (ports/depots count as network ends only if in `net`)
            # Prefer to end on a plain rail tile: a click onto a town/port tile was not accepted in play (linking onto (47,48) was), so structure tiles are goals only as a fallback.
            for goals in ({j for j in net if not tiles[j * rm.STRIDE + 0x1c]}, net):
                prev = {d: None}; queue = [d]; goal = None
                while queue and goal is None:
                    nxt = []
                    for i in queue:
                        for b, t in nbrs(i):
                            j = idx(t)
                            if j in prev:
                                continue
                            if j in goals:
                                prev[j] = i; goal = j; break
                            if can(j):
                                prev[j] = i; nxt.append(j)
                        if goal is not None:
                            break
                    queue = nxt
                if goal is not None:
                    break
            if goal is None:
                continue
            path = []; k = goal
            while k is not None:
                path.append(k); k = prev[k]
            path.reverse()            # depot ... goal
            for a, b2 in zip(path, path[1:]):
                bit = [rm.linked_tile(a, bb) for bb in range(6)].index((b2 % W, b2 // W))
                if not (rail(a) >> bit & 1):
                    if a in occupied or b2 in occupied:      # another unit stands there: clicking it opens its Civilian Report instead of giving an order
                        break
                    dist = abs(a % W - o[0]) + abs(a // W - o[1])
                    if best is None or dist < best[0]:
                        best = (dist, a, b2)
                    break
        if best is None:
            print('none'); return
        _, a, b2 = best
        here = o[1] * W + o[0]
        for tile, word in ((b2, 'lay'), (a, 'move')) if here == a else ((a, 'move'),):
            mx, my, gx, gy = to_game(tile % W, tile // W, o[0], o[1])
            if 60 < mx < 1000 and 120 < my < 940:
                print('%s %d %d' % (word, gx, gy)); return
        print('none'); return
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
