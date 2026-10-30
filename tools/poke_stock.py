"""TEST FIXTURE ONLY: set the local human's goods stock (and/or labor) in the running game so a shortage can be set up.
Orders must still be set through the real UI, so the game's own SetAmount/Complete code is what gets tested.
Usage: python -I poke_stock.py Wool=1 Cotton=10 labor=5     (names: the 17 goods, grain/fruit/fish/meat, labor)"""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys

AUTO_VT = 0x654088
G_POWERS = 0x6a4370
NAMES = ['Cotton', 'Wool', 'Timber', 'Coal', 'Iron', 'Horses', 'Oil', 'Food', 'Fabric', 'Lumber', 'Paper', 'Steel', 'Fuel',
         'Clothing', 'Furniture', 'Hardware', 'Arms', 'grain', 'fruit', 'fish', 'meat']

pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)   # VM_READ | VM_WRITE | VM_OPERATION | QUERY
assert h, 'OpenProcess failed'


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    assert k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)), 'read %x' % addr
    return buf.raw


def wr(addr, data):
    put = ctypes.c_size_t()
    assert k32.WriteProcessMemory(h, ctypes.c_void_p(addr), data, len(data), ctypes.byref(put)) and put.value == len(data), 'write %x' % addr


u32 = lambda a: struct.unpack('<I', rd(a, 4))[0]
nations = [u32(G_POWERS + 4 * i) for i in range(7)]
human = [n for n in nations if n and u32(n) != AUTO_VT]
assert len(human) == 1
city = u32(human[0] + 0x894); labor_obj = u32(city + 0x1d8)
for arg in sys.argv[1:]:
    k, v = arg.split('='); v = int(v)
    if k == 'labor':
        addr = labor_obj + 0x1c
    else:
        addr = city + 0xb6 + 2 * [n.lower() for n in NAMES].index(k.lower())
    old = struct.unpack('<h', rd(addr, 2))[0]
    wr(addr, struct.pack('<h', v))
    print('%s: %d -> %d' % (k, old, v))
