"""Read-only: list a nation's built structures (capital, ports, depots) and whether each is CONNECTED to the capital, from memory.
The structures are 0x50-byte objects (vtable 0x66d7c8) in an MFC pointer list at Great Power +0x898 (created by 0x5145b0 for depots and 0x5147d0 for ports);
the list object is {vtable, ?, head node, tail node, count, ...} and each node is {next, prev, data}.
Object fields (seen 2026-11-01 by dumping the same depot unconnected and then after rail reached the capital; only +0x4c changed 0 -> 1):
  +0x14 short  tile index (y * 108 + x)           +0x1a short  turn built (capital 0)           +0x1c dword  owning nation
  +0x4c byte   CONNECTED to the capital (1 for the capital and for ports, which are always connected; 0 -> 1 for a depot when rail links it)
  +0x4d byte   has a port      +0x4f byte   has a depot      (+0x4e: uninitialised garbage)
Usage: python -I readstructs.py [nation_index]      (default: the local human power from readcity.py)"""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
W = 108
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)


def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t()
    return b.raw if k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)) else None


out = subprocess.check_output([sys.executable, '-I', RE + 'tools/readcity.py', 'now']).decode()
gp = [int(x, 16) for x in out.split('great powers')[1].split('[')[1].split(']')[0].replace("'", '').split(',')]
local = int(out.split('client (local human) powers: [(')[1].split(',')[0])
n = int(sys.argv[1]) if len(sys.argv) > 1 else local
lst = struct.unpack('<I', rd(gp[n] + 0x898, 4))[0]
head, tail, count = struct.unpack_from('<III', rd(lst, 20), 8)
print('nation %d: %d structures' % (n, count))
node = head
for _ in range(count + 2):
    if not node: break
    nxt, prv, data = struct.unpack('<III', rd(node, 12))
    o = rd(data, 0x50)
    tile, = struct.unpack_from('<H', o, 0x14); built, = struct.unpack_from('<H', o, 0x1a); nat, = struct.unpack_from('<I', o, 0x1c)
    kinds = ','.join(name for off, name in ((0x4d, 'port'), (0x4f, 'depot')) if o[off]) or 'none'
    print('  (%d,%d) %-11s built turn %-3d nation %d  connected=%d' % (tile % W, tile // W, kinds, built, nat, o[0x4c]))
    node = nxt
