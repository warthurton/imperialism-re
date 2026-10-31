"""Read-only: dump the game's TDiplomacyMgr (pointer in global 0x6a43d0, 6364 bytes) from the running Imperialism.exe.
Three 23x23 short matrices (nation x nation; 0-6 = the seven Great Powers, 7-22 = the sixteen Minor Nations):
  +0x79c  relationship score 0..255 (symmetric; below 50 only while at war)          TDiplomacyMgr_vf10 sets it
  +0xbbe  treaty status code (symmetric; 6 = war, 2 = counted as an ally by vf35)      vf28 reads it, vf29/vf30 set it
  +0xfe0  game turn the status last changed (symmetric)
  +0x1402 diplomatic presence (symmetric): 0 none, 1 Trade Consulate, 2 Embassy     TDiplomacyMgr_GetPresence reads it
plus the 16-entry short tables at +0x1886 (Great Power with the best relationship) and +0x18a6 (favourite trading partner), both indexed by nation number 7-22 (entries 0-6 unused).
Usage: python -I readdiplo.py <label> [--full]    saves results/diplo_<label>.bin; prints a summary (--full prints all three matrices)
       python -I readdiplo.py diff <a> <b>         prints every matrix cell that differs between two saved dumps"""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
G_DIPLO = 0x6a43d0
SIZE = 6364
N = 23
MATS = {'relation': 0x79c, 'status': 0xbbe, 'turn': 0xfe0, 'presence': 0x1402}


def label(i):
    return 'G%d' % i if i < 7 else 'M%d' % i


def mat(raw, off):
    return [[struct.unpack('<h', raw[off + (r * N + c) * 2: off + (r * N + c) * 2 + 2])[0] for c in range(N)] for r in range(N)]


if sys.argv[1] == 'diff':
    a = open(RE + 'results/diplo_%s.bin' % sys.argv[2], 'rb').read(); b = open(RE + 'results/diplo_%s.bin' % sys.argv[3], 'rb').read()
    for name, off in MATS.items():
        ma, mb = mat(a, off), mat(b, off)
        for r in range(N):
            for c in range(r, N):                      # symmetric: list each pair once
                if ma[r][c] != mb[r][c]:
                    print('%-8s %s-%s  %d -> %d' % (name, label(r), label(c), ma[r][c], mb[r][c]))
    for off, n in ((0x1886, 16), (0x18a6, 16)):
        ta = struct.unpack('<%dh' % n, a[off:off + 2 * n]); tb = struct.unpack('<%dh' % n, b[off:off + 2 * n])
        for i in range(n):
            if ta[i] != tb[i]:
                print('table +0x%x[%d]  %d -> %d' % (off, i, ta[i], tb[i]))
    sys.exit()

pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
assert h, 'OpenProcess failed'


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    assert k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)), 'read %x' % addr
    return buf.raw


mgr = struct.unpack('<I', rd(G_DIPLO, 4))[0]
raw = rd(mgr, SIZE)
os.makedirs(RE + 'results', exist_ok=True)
open(RE + 'results/diplo_%s.bin' % sys.argv[1], 'wb').write(raw)
print('TDiplomacyMgr at %x, vtable %08x' % (mgr, struct.unpack('<I', raw[:4])[0]))
for name, off in MATS.items():
    m = mat(raw, off)
    vals = {}
    for r in range(N):
        for c in range(r, N):
            vals.setdefault(m[r][c], []).append('%s-%s' % (label(r), label(c)))
    print('%s matrix: %d distinct values' % (name, len(vals)))
    for v in sorted(vals):
        cells = vals[v]
        print('   %5d  x%-3d %s' % (v, len(cells), ' '.join(cells[:14]) + (' ...' if len(cells) > 14 else '')))
    if '--full' in sys.argv:
        print('      ' + ' '.join('%4s' % label(c) for c in range(N)))
        for r in range(N):
            print('%4s  ' % label(r) + ' '.join('%4d' % m[r][c] for c in range(N)))
for off in (0x1886, 0x18a6):
    print('table +0x%x:' % off, list(struct.unpack('<16h', raw[off:off + 32])))
