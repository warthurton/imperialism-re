"""TEST FIXTURE ONLY (writes game memory; document every use, see docs/map.md): set one byte of a map tile.
Usage: python -I poke_tile.py <x> <y> <offset_hex> <value>        e.g. poke_tile.py 47 49 0x06 36
Tiles are 0x24 bytes at map manager +0xc (global 0x6a43d4), index = y * 108 + x. Never use this while just playing the game (hidden-information rule)."""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys

x, y, off, val = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3], 0), int(sys.argv[4], 0)
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k = ctypes.WinDLL('kernel32', use_last_error=True); k.OpenProcess.restype = wt.HANDLE
h = k.OpenProcess(0x0010 | 0x0020 | 0x0008, False, pid)
assert h, 'OpenProcess failed'
def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t()
    assert k.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)); return b.raw
mm = struct.unpack('<I', rd(0x6a43d4, 4))[0]
tiles = struct.unpack('<I', rd(mm + 0xc, 4))[0]
addr = tiles + (y * 108 + x) * 0x24 + off
old = rd(addr, 1)[0]
g = ctypes.c_size_t()
assert k.WriteProcessMemory(h, ctypes.c_void_p(addr), bytes([val]), 1, ctypes.byref(g)), 'write failed'
print('tile (%d,%d) +0x%02x: %d -> %d (at %08x)' % (x, y, off, old, val, addr))
