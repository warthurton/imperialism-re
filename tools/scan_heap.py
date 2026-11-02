"""Read-only research helper: find every aligned dword in the whole game process (heap and image) that equals one of the given values.
Usage: python -I scan_heap.py <out.json> <hex value> [<hex value> ...]       writes {value: [addresses]} and prints the counts
Compare two runs with `python -I scan_heap.py diff a.json b.json` (addresses that point at a value in one run and at another in the other)."""
import ctypes, ctypes.wintypes as wt, json, struct, subprocess, sys

if sys.argv[1] == 'diff':
    a, b = json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
    where_a = {ad: v for v, l in a.items() for ad in l}; where_b = {ad: v for v, l in b.items() for ad in l}
    for ad in sorted(set(where_a) | set(where_b), key=int):
        if where_a.get(ad) != where_b.get(ad):
            print('%08x: %s -> %s' % (int(ad), where_a.get(ad), where_b.get(ad)))
    sys.exit()

out = sys.argv[1]; vals = [int(x, 16) for x in sys.argv[2:]]
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)


class MBI(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_void_p), ('AllocBase', ctypes.c_void_p), ('AllocProt', wt.DWORD), ('Size', ctypes.c_size_t), ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


res = {'%08x' % v: [] for v in vals}
packed = {struct.pack('<I', v): '%08x' % v for v in vals}
addr = 0x10000
mbi = MBI()
while addr < 0x7ffe0000 and k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    base, size = mbi.Base or 0, mbi.Size
    if mbi.State == 0x1000 and not (mbi.Protect & 0x101) and size < 0x10000000:   # committed, not NOACCESS/GUARD
        buf = ctypes.create_string_buffer(size); got = ctypes.c_size_t()
        if k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)):
            data = buf.raw[:got.value]
            for pk, name in packed.items():
                i = data.find(pk)
                while i != -1:
                    if i % 4 == 0: res[name].append(base + i)
                    i = data.find(pk, i + 1)
    addr = base + size
json.dump(res, open(out, 'w'))
print({k: len(v) for k, v in res.items()})
