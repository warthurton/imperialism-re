"""Read-only snapshot of the local human power's TCity from the running Imperialism.exe (no writes, ever).
Usage: python -I readcity.py [label]   -> prints a decoded summary and saves raw bytes to results/city_<label>.json"""
import ctypes, ctypes.wintypes as wt, json, os, struct, subprocess, sys

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
AUTO_VT = 0x654088
G_POWERS = 0x6a4370

pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)   # VM_READ | QUERY_INFORMATION only
assert h, 'OpenProcess failed'


def rd(addr, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got))
    assert ok, 'read failed at %x' % addr
    return buf.raw


u32 = lambda a: struct.unpack('<I', rd(a, 4))[0]
shorts = lambda a, n: list(struct.unpack('<%dh' % n, rd(a, 2 * n)))

nations = [u32(G_POWERS + 4 * i) for i in range(7)]
print('vtables', [hex(u32(n)) if n else None for n in nations])
# the local human is the one great power whose vtable is not TAutoGreatPower's (0x654088) in a single-player game
client = [(i, n) for i, n in enumerate(nations) if n and u32(n) != AUTO_VT]
print('great powers', [hex(n) for n in nations])
print('client (local human) powers:', [(i, hex(n)) for i, n in client])
assert len(client) == 1, 'expected exactly one TClientGreatPower'
idx, nat = client[0]
city = u32(nat + 0x894)
assert city, 'city pointer is null (not on the map yet?)'
labor_obj = u32(city + 0x1d8)
snap = {'nation_index': idx, 'nation': nat, 'city': city,
        'city_raw': rd(city, 0x300).hex(), 'labor_raw': rd(labor_obj, 0x40).hex()}
orders = {}
for slot in range(61):
    p = u32(city + 0xe4 + 4 * slot)
    if p:
        orders[slot] = {'ptr': p, 'raw': rd(p, 0x54).hex()}
snap['orders'] = orders

G = ['Cotton', 'Wool', 'Timber', 'Coal', 'Iron', 'Horses', 'Oil', 'Food', 'Fabric', 'Lumber', 'Paper', 'Steel', 'Fuel',
     'Clothing', 'Furniture', 'Hardware', 'Arms']
CAT = ['Textile', 'ClothFact', 'SteelMill', 'MetalWks', 'LumberMill', 'FurnFact', 'Refinery']
st = shorts(city + 0xb6, 23)
print('turn counter city+0xc :', shorts(city + 0xc, 1)[0])
print('stock    +0xb6 :', {G[i]: st[i] for i in range(17) if st[i]}, 'grain/fruit/fish/meat', st[17:21], 'other', st[21:])
print('+0x7e (AI bonus?) :', {G[i]: v for i, v in enumerate(shorts(city + 0x7e, 17)) if v})
print('arrivals +0x2a6 :', {G[i]: v for i, v in enumerate(shorts(city + 0x2a6, 17)) if v})
print('cap_max  +0x1dc :', dict(zip(CAT, shorts(city + 0x1dc, 7))))
print('cap_left +0x1fc :', dict(zip(CAT, shorts(city + 0x1fc, 7))))
print('labor obj +0x1c / +0x1e :', shorts(labor_obj + 0x1c, 2), ' pools +4/+6/+8:', shorts(labor_obj + 4, 3))
owner = u32(city + 0xac)
print('cash   owner+0x10 :', struct.unpack('<i', rd(owner + 0x10, 4))[0])
try:
    p1, p2 = u32(labor_obj + 0x10), u32(labor_obj + 0x14)
    print('workers  untrained/trained(+4 of labor+0x10/+0x14) :', shorts(p1 + 4, 1)[0], shorts(p2 + 4, 1)[0], ' labor+8 total:', shorts(labor_obj + 8, 1)[0])
except AssertionError:
    pass
print('score city+0x78 :', struct.unpack('<i', rd(city + 0x78, 4))[0])
for slot, o in orders.items():
    r = bytes.fromhex(o['raw'])
    amt = struct.unpack_from('<h', r, 4)[0]; item = struct.unpack_from('<h', r, 0x48)[0]
    resv = struct.unpack_from('<23h', r, 0x10) if len(r) >= 0x10 + 46 else ()
    if amt or any(resv):
        print('order slot %d item %d amount %d reserved %s remembered(+0x4c) %d binding(+0x40) %d' % (
            slot, item, amt, {G[i]: v for i, v in enumerate(resv[:17]) if v}, struct.unpack_from('<h', r, 0x4c)[0],
            struct.unpack_from('<h', r, 0x40)[0]))
label = sys.argv[1] if len(sys.argv) > 1 else 'snap'
os.makedirs(RE + 'results', exist_ok=True)
json.dump(snap, open(RE + 'results/city_%s.json' % label, 'w'))
print('saved results/city_%s.json' % label)
