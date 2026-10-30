"""Find which vtable(s) reference a function (via its address or its incremental-link jmp stub) and at which slot.
Usage: python -I find_vtable_refs.py 004538a0 [...]   -> prints class vtable name and slot."""
import struct, sys, json, os
RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
d = open('C:/GOG Games/Imperialism/Imperialism.exe', 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]; nsec = struct.unpack_from('<H', d, pe + 6)[0]; opt = struct.unpack_from('<H', d, pe + 20)[0]
base = struct.unpack_from('<I', d, pe + 24 + 28)[0]
S = [(d[pe+24+opt+i*40:pe+24+opt+i*40+8].rstrip(b'\0'),) + struct.unpack_from('<IIII', d, pe+24+opt+i*40+8) for i in range(nsec)]
vt = sorted((int(k, 16), v) for k, v in json.load(open(RE + 'renames.json'))['vtables'].items())


def off(va):
    for n, vs, v, rs, ro in S:
        if base + v <= va < base + v + max(vs, rs): return ro + va - base - v


def stub_for(t):
    out = {t}
    text = next(s for s in S if s[0] == b'.text')
    ro, rs = text[4], text[3]
    for o in range(0, min(rs, 0xb000)):
        if d[ro + o] == 0xE9 and base + text[2] + o + 5 + struct.unpack_from('<i', d, ro + o + 1)[0] == t:
            out.add(base + text[2] + o)
    return out


for arg in sys.argv[1:]:
    t = int(arg, 16); targets = stub_for(t); found = False
    for n, vs, v, rs, ro in S:
        if n not in (b'.rdata', b'.data'): continue
        for o in range(0, rs - 3, 4):
            if struct.unpack_from('<I', d, ro + o)[0] in targets:
                a = base + v + o
                cand = [(s, nm) for s, nm in vt if s <= a]
                s, nm = cand[-1] if cand else (0, '?')
                print('%s referenced at %08x: %s slot %d (+0x%x)' % (arg, a, nm, (a - s) // 4, a - s)); found = True
    if not found: print(arg, 'no vtable reference')
