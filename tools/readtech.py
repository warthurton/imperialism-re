"""Read-only: find the TTechMgr object (vtable 0x66ad28, 0x63c bytes) in the running Imperialism.exe's heap and print its
known-tech byte array (+0x180, 29 entries) and the other per-tech arrays. No writes. Usage: python -I readtech.py [label]
Saves the raw object to results/tech_<label>.bin"""
import ctypes, ctypes.wintypes as wt, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
VT = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x66ad28
label = sys.argv[1] if len(sys.argv) > 1 else 'now'
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
assert h, 'OpenProcess failed'


class MBI(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_void_p), ('AllocBase', ctypes.c_void_p), ('AllocProt', wt.DWORD), ('Size', ctypes.c_size_t),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


hits = []
addr = 0x10000
pat = struct.pack('<I', VT)
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
                    hits.append(mbi.Base + i)
                i = raw.find(pat, i + 1)
    addr = (mbi.Base or addr) + mbi.Size
print('TTechMgr candidates:', [hex(x) for x in hits])
for a in hits:
    buf = ctypes.create_string_buffer(0x63c); got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(a), buf, 0x63c, ctypes.byref(got)):
        continue
    raw = buf.raw
    os.makedirs(RE + 'results', exist_ok=True)
    open(RE + 'results/tech_%s.bin' % label, 'wb').write(raw)
    print('object at %x' % a)
    print('+0x180 (29):', list(raw[0x180:0x180 + 29]))
    print('+0x19d (14):', list(raw[0x19d:0x19d + 14]))
    print('+0x1ab (30):', list(raw[0x1ab:0x1ab + 30]))
    print('+0x1c9 (9):', list(raw[0x1c9:0x1c9 + 9]))
    print('+0x1d2,+0x1d4 shorts:', struct.unpack('<2h', raw[0x1d2:0x1d6]))
    break
