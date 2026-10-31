"""Read-only: print the local human Great Power's pending-overture table (23 shorts at nation+0xb2, one per target nation, 0xFFFF = none)
from the running Imperialism.exe, plus its cash. Nation numbers: 0-6 Great Powers, 7-22 Minor Nations.
Usage: python -I readpending.py [offset]      (default 0xb2; try other offsets while hunting for related tables)"""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys

G_NATIONS = 0x6a4310
G_GAME = 0x6a20f8
base = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0xb2
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
assert h, 'OpenProcess failed'


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    assert k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)), 'read %x' % addr
    return buf.raw


game = struct.unpack('<I', rd(G_GAME, 4))[0]
local = struct.unpack('<h', rd(game + 0x2e, 2))[0]
nat = struct.unpack('<I', rd(G_NATIONS + 4 * local, 4))[0]
tab = struct.unpack('<23H', rd(nat + base, 46))
cash = struct.unpack('<i', rd(nat + 0x10, 4))[0]
print('local power %d, cash %d' % (local, cash))
for n, v in enumerate(tab):
    if v != 0xFFFF:
        print('  target %2d (%s): 0x%03x = %d' % (n, 'G' if n < 7 else 'M', v, v))
if all(v == 0xFFFF for v in tab):
    print('  (no pending overtures)')
