"""TEST FIXTURE ONLY: mark technologies as known in the running game's TTechMgr (the byte array at +0x180, one byte per tech in
the order of the tech name strings 17161+index: 1 High Pressure Steam Engine ... 19 Oil Drilling, which the game itself tests as
byte +0x193 before showing Oil). The game's own grant routine FUN_005afba0 sets this byte plus side flags for a few techs; Oil is
not one of them. Orders are still placed through the real UI so the game's own code is what gets tested.
Usage: python -I poke_tech.py 19 1:19     (N = global known flag; P:T = power P owns tech T, value 2, P may be L for the local human; negative T clears)"""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys

VT = 0x66ad28
BASE = 0x180
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)   # VM_READ | VM_WRITE | VM_OPERATION | QUERY
assert h, 'OpenProcess failed'


class MBI(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_void_p), ('AllocBase', ctypes.c_void_p), ('AllocProt', wt.DWORD), ('Size', ctypes.c_size_t),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


def find():
    pat = struct.pack('<I', VT); out = []; addr = 0x10000
    while addr < 0x7ff00000:
        mbi = MBI()
        if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and mbi.Protect in (0x04, 0x08, 0x40, 0x80) and mbi.Size < 0x10000000:
            buf = ctypes.create_string_buffer(mbi.Size); got = ctypes.c_size_t()
            if k32.ReadProcessMemory(h, ctypes.c_void_p(mbi.Base), buf, mbi.Size, ctypes.byref(got)):
                raw = buf.raw[:got.value]; i = raw.find(pat)
                while i != -1:
                    if i % 4 == 0:
                        out.append(mbi.Base + i)
                    i = raw.find(pat, i + 1)
        addr = (mbi.Base or addr) + mbi.Size
    return out


objs = find()
assert len(objs) == 1, 'expected exactly one TTechMgr, found %s' % [hex(x) for x in objs]
obj = objs[0]
for arg in sys.argv[1:]:
    if ':' in arg:                      # "P:T" = power P (0-6) owns tech T: per-power record at +0x268 + P*29 + T, value 2 (0 clears)
        p, t = arg.split(':'); idx = abs(int(t)); val = 0 if int(t) < 0 else 2
        if p.upper() == 'L':            # L = the local human power, g_Game+0x2e (it is NOT always 0: it changes between new games)
            gb = ctypes.create_string_buffer(4); gg = ctypes.c_size_t()
            assert k32.ReadProcessMemory(h, ctypes.c_void_p(0x6a20f8), gb, 4, ctypes.byref(gg))
            pb = ctypes.create_string_buffer(2)
            assert k32.ReadProcessMemory(h, ctypes.c_void_p(struct.unpack('<I', gb.raw)[0] + 0x2e), pb, 2, ctypes.byref(gg))
            p = struct.unpack('<h', pb.raw)[0]; print('local power index', p)
        p = int(p)
        assert 0 <= p < 7 and 0 <= idx < 29
        a = obj + 0x268 + p * 29 + idx
    else:
        n = int(arg); val = 0 if n < 0 else 1; idx = abs(n)
        assert 0 <= idx < 29
        a = obj + BASE + idx
    old = ctypes.create_string_buffer(1); got = ctypes.c_size_t()
    assert k32.ReadProcessMemory(h, ctypes.c_void_p(a), old, 1, ctypes.byref(got))
    put = ctypes.c_size_t()
    assert k32.WriteProcessMemory(h, ctypes.c_void_p(a), bytes([val]), 1, ctypes.byref(put)) and put.value == 1
    print('tech %d at %x: %d -> %d' % (idx, a, old.raw[0], val))
