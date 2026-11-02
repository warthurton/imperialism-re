"""Read-only: decode the game's map from memory (no screenshots). The map manager is the pointer in global 0x6a43d4 (g_MapMgr);
tiles are 6,480 records of 0x24 bytes at +0xc, a 108 x 60 grid (index = y * 108 + x); provinces are 120 used records of 0xa8 bytes at +0x10.
Usage: python -I readmap.py summary                       counts per terrain / kind / owner
       python -I readmap.py ascii [nation]                the grid as terrain letters (whole world, or only the nation's provinces)
       python -I readmap.py find <kind> [nation] [--unprospected]    list tiles of a kind (e.g. mountain, hills, forest, sea) in a nation
       python -I readmap.py structures [nation]           towns, capitals, ports, depots and rail pieces (with the tiles they link to) and their gatherer ids
       python -I readmap.py units [nation]            tiles that carry a unit pointer (+0x20), with the pointer and its vtable
       python -I readmap.py dump <file>                   save the raw tile bytes (results/*.bin is git-ignored)
       python -I readmap.py diff <a.bin> <b.bin>          changed tiles, ignoring the viewport index (+0x10)
Field decode (CONFIRMED = seen against the running game and the code; GUESS = only a pattern in the data, see docs/map.md):
  tile +0x00 terrain  0 plain 1 forest 2 hills 3 mountain 4 swamp-like 5 sea 6 desert/tundra-like 7 farmland   CONFIRMED (names for 4 and 6 are a guess)
  tile +0x13 kind     1 dry plains 2 plantation 3 open range 4 horse ranch 5 farm 6 orchard 7 fertile hills 8 barren hills 9 mountain
                      10 oil-type A 11-12 oil-type B 13 scrub forest 15 hardwood forest (14: one tile)                     CONFIRMED by crosstab with the card tables
  tile +0x11, +0x12   resource slot 1 and 2, signed byte, -1 = none: 0 cotton 1 wool 2 timber 3 coal 4 iron 5 horses 6 oil 17 grain 18 fruit
                      19 fish 20 livestock 21 gold 22 gems. The game stores hidden deposits here too (shown only once prospected).   CONFIRMED (code + crosstab)
  tile +0x0d          PROSPECTED bit mask: bit n = Great Power n has searched this tile (prospect completion does `+0x0d |= 1 << nation`, 0x4d4390 case 8;
                      my nation 3 -> value 8, a tile five AIs searched = 127).   CONFIRMED by the code and the data. (An earlier version of this tool used
                      +0x01 bit 0; that was a wrong guess: +0x01 is something else, probably a deposit/terrain flag, undecoded.)
  tile +0x14 (short)  province index 0-119, 0xffff on the sea; province +0 and +1 = owning nation (same value), +4 = the town's tile index   CONFIRMED
  tile +0x20 (dword)  pointer to the unit standing on the tile (moves with the unit)                                              CONFIRMED by a moving unit
  tile +0x10          index inside the currently visible window (9 x 8 tiles); a VIEW detail that changes when the map scrolls, not game state
  tile +0x1c flags    0x04 port, 0x10 depot, 0x20 town, 0x08 national capital, 0x01/0x02 other town bits: ordinary town 0x22 (34), minor capital 0x29 (41),
                      Great Power capital 0x3f (63 = town + capital + port + depot, as the manual says), a built depot 34 -> 50, a built port 0 -> 4.   CONFIRMED by
                      the 7 + 16 capitals, my timber port and fish port, and AI ports and depots appearing in an end-turn diff; the 0x01 and 0x02 bits are a guess
  tile +0x17          the same rail mask as the LOCAL PLAYER can see it: equal to +0x06 on my own rail, 0 on every AI rail (20 tiles differ in the saved game), so it
                      looks like a fog-of-war copy. An autoplayer that plays with visible information only should read +0x17, not +0x06.   LIKELY (pattern, not tested by scouting)
  tile +0x06          true rail mask, one bit per neighbour: 0 NE, 1 E, 2 SE, 3 SW, 4 W, 5 NW; odd rows are shifted half a tile to the right, so for an odd row
                      NE = (x+1,y-1), NW = (x,y-1), SE = (x+1,y+1), SW = (x,y+1) and for an even row NE = (x,y-1), NW = (x-1,y-1), SE = (x,y+1), SW = (x-1,y+1).
                      Both ends of a rail piece carry opposite bits.   CONFIRMED on my capital-to-port line (1, 40, 4) and on AI rail appearing in a diff
  tile +0x05          id of the structure (depot, port or capital) that gathers this tile, 255 = none; a depot or port claims its own tile and the six neighbours that are
                      land and not already claimed (my capital 4, timber port 2, fish port 3)   CONFIRMED pattern, meaning of the id numbers unknown
  tile +0x0c, +0x0d, +0x02, +0x16, +0x19, +0x1e, +0x03/+0x04   undecoded (+0x0c = 1 on the capital and two coastal neighbours)
Checked: all 36 rail links in the whole world are reciprocal (a piece pointing at a neighbour is pointed back at), which confirms the bit order and the staggered-row geometry.
Not yet tested: developed levels; fog for ports/depots; no controlled Engineer build was run (the evidence is the saved game's existing structures plus one end-turn diff).
"""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys, collections

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
G_MAPMGR = 0x6a43d4
W, H, N, STRIDE, PSTRIDE = 108, 60, 6480, 0x24, 0xa8
TERRAIN = {0: 'plain', 1: 'forest', 2: 'hills', 3: 'mountain', 4: 'swamp?', 5: 'sea', 6: 'desert?', 7: 'farmland'}
LETTER = {0: ',', 1: 'f', 2: 'h', 3: 'M', 4: 's', 5: '.', 6: 'd', 7: 'F'}
KIND = {1: 'dry plains', 2: 'plantation', 3: 'open range', 4: 'horse ranch', 5: 'farm', 6: 'orchard', 7: 'fertile hills', 8: 'barren hills',
        9: 'mountain', 10: 'oil-type A', 11: 'oil-type B', 12: 'oil-type B', 13: 'scrub forest', 14: 'other', 15: 'hardwood forest'}
RES = {0: 'cotton', 1: 'wool', 2: 'timber', 3: 'coal', 4: 'iron', 5: 'horses', 6: 'oil', 17: 'grain', 18: 'fruit', 19: 'fish', 20: 'livestock', 21: 'gold', 22: 'gems'}
# words usable on the command line for `find`
FIND = {'sea': (0, 5), 'plain': (0, 0), 'forest': (0, 1), 'hills': (0, 2), 'mountain': (0, 3), 'farmland': (0, 7)}


class Game:
    def __init__(self):
        pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command',
                                           '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
        self.k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k32.OpenProcess.restype = wt.HANDLE
        self.h = self.k32.OpenProcess(0x0010 | 0x0400, False, pid)
        assert self.h, 'OpenProcess failed (is the game running?)'

    def rd(self, addr, n):
        buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
        assert self.k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)), 'read %x' % addr
        return buf.raw

    def load(self):
        mm = struct.unpack('<I', self.rd(G_MAPMGR, 4))[0]
        tiles = self.rd(struct.unpack('<I', self.rd(mm + 0xc, 4))[0], N * STRIDE)
        prov = self.rd(struct.unpack('<I', self.rd(mm + 0x10, 4))[0], 120 * PSTRIDE)
        return tiles, prov


def province_of(tiles, i):
    p = struct.unpack('<H', tiles[i * STRIDE + 0x14:i * STRIDE + 0x16])[0]
    return p if p < 120 else None


def owner_of(tiles, prov, i):
    p = province_of(tiles, i)
    return None if p is None else prov[p * PSTRIDE + 1]


def sbyte(b):
    return b - 256 if b > 127 else b


_LOCAL = []


def local_nation():
    """index of the local human power (from readcity.py's "client powers" line), looked up once"""
    if not _LOCAL:
        out = subprocess.check_output([sys.executable, '-I', RE + 'tools/readcity.py', 'now']).decode()
        _LOCAL.append(int(out.split('client (local human) powers: [(')[1].split(',')[0]))
    return _LOCAL[0]


DIRS = ['NE', 'E', 'SE', 'SW', 'W', 'NW']


def linked_tile(i, bit):
    """the neighbouring tile in rail-mask direction `bit` (0 NE, 1 E, 2 SE, 3 SW, 4 W, 5 NW); odd rows are shifted half a tile right"""
    x, y = i % W, i // W
    odd = y & 1
    dx, dy = [(1 if odd else 0, -1), (1, 0), (1 if odd else 0, 1), (0 if odd else -1, 1), (-1, 0), (0 if odd else -1, -1)][bit]
    return x + dx, y + dy


def tile_info(tiles, prov, i):
    r = tiles[i * STRIDE:(i + 1) * STRIDE]
    res = [RES.get(sbyte(r[o]), str(sbyte(r[o]))) for o in (0x11, 0x12) if sbyte(r[o]) != -1]
    unit = struct.unpack('<I', r[0x20:0x24])[0]
    return {'i': i, 'x': i % W, 'y': i // W, 'terrain': TERRAIN.get(r[0], str(r[0])), 'kind': KIND.get(r[0x13], str(r[0x13])), 'resources': res,
            'prospected_by': [n for n in range(8) if r[0x0d] >> n & 1], 'prospected': bool(r[0x0d] >> local_nation() & 1), 'province': province_of(tiles, i), 'owner': owner_of(tiles, prov, i), 'unit_ptr': unit or None}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'summary'
    if cmd == 'diff':
        a, b = open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read()
        n = 0
        for i in range(N):
            ra, rb = a[i * STRIDE:(i + 1) * STRIDE], b[i * STRIDE:(i + 1) * STRIDE]
            d = {'+%02x' % o: (ra[o], rb[o]) for o in range(STRIDE) if ra[o] != rb[o] and o != 0x10}
            if d:
                n += 1; print(i, (i % W, i // W), d)
        print(n, 'tiles changed (viewport index +0x10 ignored)'); return
    g = Game(); tiles, prov = g.load()
    if cmd == 'dump':
        open(sys.argv[2], 'wb').write(tiles); print('saved', sys.argv[2]); return
    nation = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    if cmd == 'summary':
        c = collections.Counter(tiles[i * STRIDE] for i in range(N))
        print('terrain:', {TERRAIN[k]: v for k, v in sorted(c.items())})
        o = collections.Counter(owner_of(tiles, prov, i) for i in range(N) if owner_of(tiles, prov, i) is not None)
        print('land tiles by owning nation:', dict(sorted(o.items())))
    elif cmd == 'ascii':
        for y in range(H):
            row = ''
            for x in range(W):
                i = y * W + x
                row += LETTER.get(tiles[i * STRIDE], '?') if nation is None or owner_of(tiles, prov, i) == nation or tiles[i * STRIDE] == 5 and False else ' '
            if row.strip(): print('%2d %s' % (y, row))
    elif cmd == 'find':
        word = sys.argv[2]; nation = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None
        only_un = '--unprospected' in sys.argv
        for i in range(N):
            r = tiles[i * STRIDE:(i + 1) * STRIDE]
            info = tile_info(tiles, prov, i)
            ok = (word in FIND and r[0] == FIND[word][1]) or word == info['kind'] or word in info['resources']
            if ok and (nation is None or info['owner'] == nation) and (not only_un or not info['prospected']):
                print(info)
    elif cmd == 'structures':
        for i in range(N):
            r = tiles[i * STRIDE:(i + 1) * STRIDE]
            info = tile_info(tiles, prov, i)
            if nation is not None and info['owner'] != nation:
                continue
            f, rail = r[0x1c], r[0x06]
            names = [n for bit, n in ((0x08, 'capital'), (0x04, 'port'), (0x10, 'depot'), (0x20, 'town')) if f & bit]
            if names or rail:
                links = [linked_tile(i, b) for b in range(6) if rail & (1 << b)]
                print('(%d,%d) %s%s%s gatherer id %s' % (info['x'], info['y'], ','.join(names) or 'rail',
                      ' rail ' + ' '.join('%s->(%d,%d)' % (DIRS[b], *linked_tile(i, b)) for b in range(6) if rail & (1 << b)) if rail else '',
                      ' [owner %s]' % info['owner'], r[5] if r[5] != 255 else '-'))
    elif cmd == 'units':
        for i in range(N):
            info = tile_info(tiles, prov, i)
            if info['unit_ptr'] and (nation is None or info['owner'] == nation):
                try: vt = '%08x' % struct.unpack('<I', g.rd(info['unit_ptr'], 4))[0]
                except Exception: vt = '?'
                print('(%d,%d) %s %s owner %s unit at %08x vtable %s' % (info['x'], info['y'], info['terrain'], info['kind'], info['owner'], info['unit_ptr'], vt))
    else:
        print(__doc__)


main()
