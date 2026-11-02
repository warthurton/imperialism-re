"""Read-only: a nation's civilians (TCivUnit objects, 40 bytes, vtable 0x66ee60) and the currently selected unit.
The civilian list is an MFC pointer list at Great Power +0x89c (next to the structures list at +0x898); each node is {next, prev, data}.
The selected unit is at *(*0x6a43dc + 4) (0x6a43dc holds a small object, found 2026-11-01 by watching which heap word changed on Next Unit).
Usage: python -I readunits.py [nation_index] [raw]       default nation = the local human power; raw = dump every object
       python -I readunits.py sel                        print only the selected unit (address, type, tile)
Fields (docs/units.md has the evidence): +0x04 short type code, +0x06 short tile index, +0x08 short ?, +0x0c short target tile / -1,
+0x18 dword nation, +0x20 dword unit id, +0x24 short ?. Type codes are decoded in TYPE below (see docs/units.md for how)."""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
W = 108
TYPE = {}     # filled in docs/units.md once confirmed: code -> name
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)


def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t()
    return b.raw if k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)) else None


def u32(a):
    r = rd(a, 4)
    return struct.unpack('<I', r)[0] if r else 0


def describe(p, o):
    t, tile = struct.unpack_from('<hh', o, 4)
    return {'addr': p, 'type': t, 'name': TYPE.get(t, '?'), 'x': tile % W, 'y': tile // W, 'id': struct.unpack_from('<I', o, 0x20)[0], 'nation': struct.unpack_from('<I', o, 0x18)[0]}


if 'sel' in sys.argv:
    sel = u32(u32(0x6a43dc) + 4)
    o = rd(sel, 0x28) if sel else None
    print('no unit selected' if not o else describe(sel, o))
    sys.exit()
out = subprocess.check_output([sys.executable, '-I', RE + 'tools/readcity.py', 'now']).decode()
gp = [int(x, 16) for x in out.split('great powers')[1].split('[')[1].split(']')[0].replace("'", '').split(',')]
args = [a for a in sys.argv[1:] if a.isdigit()]
n = int(args[0]) if args else int(out.split('client (local human) powers: [(')[1].split(',')[0])
lst = u32(gp[n] + 0x89c)
head, tail, count = struct.unpack_from('<III', rd(lst, 20), 8)
sel = u32(u32(0x6a43dc) + 4)
print('nation %d: %d civilians; selected unit %08x' % (n, count, sel))
node = head
for i in range(count + 2):
    if not node: break
    nxt, prv, data = struct.unpack('<III', rd(node, 12))
    o = rd(data, 0x28)
    d = describe(data, o)
    print('  #%d %s%08x type %d %-10s tile (%d,%d) id %d  +08=%d +0c=%d +24=%d' % (
        i, '*' if data == sel else ' ', data, d['type'], d['name'], d['x'], d['y'], d['id'],
        struct.unpack_from('<h', o, 8)[0], struct.unpack_from('<h', o, 0xc)[0], struct.unpack_from('<h', o, 0x24)[0]))
    if 'raw' in sys.argv:
        print('      ', ' '.join('%02x' % b for b in o))
    node = nxt
