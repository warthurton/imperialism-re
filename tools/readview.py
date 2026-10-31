"""Read-only: dump the game's TViewMgr (pointer in global 0x6a21bc, 0xfc bytes) so the on-screen state (which screen / dialog is open)
can be told from memory instead of screenshots. No writes.
Usage: python -I readview.py <label>            -> prints the dwords and saves results/view_<label>.bin
       python -I readview.py diff <a> <b>       -> prints the dword offsets that differ between two saved dumps
       python -I readview.py id                 -> prints only the current screen id (the short at +4): 0x7db capital, 0x7dd terrain map
Dialogs (constructor, production sliders) are child windows and do not change this object."""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
G_EVENTS = 0x6a21bc
SIZE = 0xfc

if sys.argv[1] == 'diff':
    a = open(RE + 'results/view_%s.bin' % sys.argv[2], 'rb').read(); b = open(RE + 'results/view_%s.bin' % sys.argv[3], 'rb').read()
    for off in range(0, SIZE, 4):
        x, y = struct.unpack('<I', a[off:off + 4])[0], struct.unpack('<I', b[off:off + 4])[0]
        if x != y:
            print('+0x%02x  %08x -> %08x' % (off, x, y))
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


mgr = struct.unpack('<I', rd(G_EVENTS, 4))[0]
raw = rd(mgr, SIZE)
if sys.argv[1] == 'id':
    print(struct.unpack('<H', raw[4:6])[0]); sys.exit()
os.makedirs(RE + 'results', exist_ok=True)
open(RE + 'results/view_%s.bin' % sys.argv[1], 'wb').write(raw)
print('TViewMgr at %x, vtable %08x' % (mgr, struct.unpack('<I', raw[:4])[0]))
for off in range(4, SIZE, 16):
    print('+0x%02x ' % off + ' '.join('%08x' % struct.unpack('<I', raw[o:o + 4])[0] for o in range(off, min(off + 16, SIZE), 4)))
