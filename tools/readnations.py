"""Read-only: snapshot all 23 nation objects (g_Nations at 0x6a4310: nations 0-6 Great Powers, 2928 bytes; 7-22 Minor Nations, 732 bytes)
from the running Imperialism.exe, and diff two snapshots field by field. Used to find where a game action stores its result.
Usage: python -I readnations.py <label>             saves results/nations_<label>.bin
       python -I readnations.py diff <a> <b> [min_nation max_nation]   lists every 16-bit cell that changed, per nation, as +offset old -> new
Pointers and counters that move for unrelated reasons show up too: judge by the offsets (a value in a per-nation table is what we want)."""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
G_NATIONS = 0x6a4310
SIZES = [2928] * 7 + [732] * 16


def load(label):
    raw = open(RE + 'results/nations_%s.bin' % label, 'rb').read()
    out, pos = [], 0
    for s in SIZES:
        out.append(raw[pos:pos + s]); pos += s
    return out


if sys.argv[1] == 'diff':
    a, b = load(sys.argv[2]), load(sys.argv[3])
    lo = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    hi = int(sys.argv[5]) if len(sys.argv) > 5 else 22
    for n in range(lo, hi + 1):
        cells = []
        for off in range(0, SIZES[n] - 1, 2):
            x = struct.unpack('<H', a[n][off:off + 2])[0]; y = struct.unpack('<H', b[n][off:off + 2])[0]
            if x != y:
                cells.append('+0x%03x %d->%d' % (off, x, y))
        if cells:
            print('nation %2d (%s): %d cells  %s' % (n, 'G' if n < 7 else 'M', len(cells), '  '.join(cells[:12]) + (' ...' if len(cells) > 12 else '')))
    sys.exit()

pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
assert h, 'OpenProcess failed'


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    assert k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)), 'read %x' % addr
    return buf.raw


os.makedirs(RE + 'results', exist_ok=True)
blob = b''
for n in range(23):
    p = struct.unpack('<I', rd(G_NATIONS + 4 * n, 4))[0]
    blob += rd(p, SIZES[n])
open(RE + 'results/nations_%s.bin' % sys.argv[1], 'wb').write(blob)
print('saved nations_%s.bin (%d bytes)' % (sys.argv[1], len(blob)))
