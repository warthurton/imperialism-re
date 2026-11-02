"""Read-only research helper: save / diff the game's data globals (0x66f000-0x708000 by default) to find a variable that changes with the view (scroll origin, hovered tile).
Usage: python -I globdump.py save <name>            -> results/glob_<name>.bin
       python -I globdump.py diff <a> <b>           -> dwords that differ (address, a, b)
       python -I globdump.py hash <name>            -> also follows the pointers 0x6a43d4 (MapMgr, first 0x40 bytes) and 0x6a43dc, 0x6a21bc (first 0x100 bytes) into results/glob_<name>.ptrs"""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
LO, HI = 0x66f000, 0x708000
PTRS = [(0x6a43d4, 0x40), (0x6a43dc, 0x100), (0x6a21bc, 0x100)]
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)


def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t()
    return b.raw[:g.value] if k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)) else b'\0' * n


def snap():
    out = bytearray(rd(LO, HI - LO))
    for g, n in PTRS:
        p = struct.unpack('<I', rd(g, 4))[0]
        out += struct.pack('<I', g) + rd(p, n) if p else b''
    return bytes(out)


if sys.argv[1] == 'save':
    open(RE + 'results/glob_%s.bin' % sys.argv[2], 'wb').write(snap()); print('saved')
else:
    a = open(RE + 'results/glob_%s.bin' % sys.argv[2], 'rb').read(); b = open(RE + 'results/glob_%s.bin' % sys.argv[3], 'rb').read()
    base = HI - LO
    for off in range(0, min(len(a), len(b)) - 3, 4):
        x, y = struct.unpack_from('<I', a, off)[0], struct.unpack_from('<I', b, off)[0]
        if x != y:
            print('%s +%x: %08x -> %08x' % ('glob %08x' % (LO + off) if off < base else 'ptrblk', off if off < base else off - base, x, y))
