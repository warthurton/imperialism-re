"""Build classes.tsv: every class registered with a CRuntimeClass record in Imperialism.exe
(the game's own T* classes and the statically linked MFC C* classes).

A CRuntimeClass is {char *name; int size; WORD schema; CObject *(*create)(); CRuntimeClass *base; CRuntimeClass *next}.
The exe was linked incrementally, so `create` points at a `jmp rel32` stub in the ILT; we follow it.

usage: python -I build_class_table.py [exe] [out.tsv]
"""
import json, re, struct, sys

EXE = sys.argv[1] if len(sys.argv) > 1 else 'C:/GOG Games/Imperialism/Imperialism.exe'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'C:/GOG Games/Imperialism-RE/classes.tsv'

b = open(EXE, 'rb').read()
pe = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]
opt = struct.unpack_from('<H', b, pe + 20)[0]
base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
secs = []
for i in range(nsec):
    s = b[pe + 24 + opt + 40 * i: pe + 24 + opt + 40 * i + 40]
    vs, va, rs, rp = struct.unpack_from('<IIII', s, 8)
    secs.append((s[:8].rstrip(b'\0').decode(), va, vs, rp, rs))


def va2off(v):
    for nm, rv, vs, rp, rs in secs:
        if base + rv <= v < base + rv + max(vs, rs):
            return rp + v - base - rv


def off2va(o):
    for nm, rv, vs, rp, rs in secs:
        if rp <= o < rp + rs:
            return base + rv + o - rp


def follow(v):
    o = va2off(v)
    return v + 5 + struct.unpack_from('<i', b, o + 1)[0] if o is not None and b[o] == 0xE9 else v


names = {}
for m in re.finditer(rb'\b[CT][A-Z][A-Za-z0-9]{2,40}\b(?=\x00)', b):
    names.setdefault(m.group().decode(), off2va(m.start()))

classes = {}
for n, v in names.items():
    p = struct.pack('<I', v)
    i = b.find(p)
    while i >= 0:
        if i % 4 == 0 and i + 24 <= len(b):
            nm, size, schema, create, base_, nxt = struct.unpack_from('<IiIIII', b, i)
            if 0 < size < 0x10000 and (create == 0 or 0x401000 <= create < 0x700000) and (base_ == 0 or va2off(base_)):
                classes[n] = dict(va=off2va(i), size=size, create=create, base=base_)
                break
        i = b.find(p, i + 1)

byva = {c['va']: n for n, c in classes.items()}
rows = []
for n, c in sorted(classes.items()):
    stub = c['create']
    rows.append([n, str(c['size']), hex(c['va']), hex(stub) if stub else '-',
                 byva.get(c['base']) or hex(c['base']), hex(follow(stub)) if stub else '-'])
with open(OUT, 'w', newline='') as f:
    f.write('class\tsize\tclassVA\tfactoryStub\tbase\tfactoryReal\n')
    for r in rows:
        f.write('\t'.join(r) + '\n')
mfc = [r for r in rows if r[0].startswith('C')]
print(len(rows), 'classes;', len(mfc), 'MFC-style (C*);', sum(1 for r in mfc if r[5] != '-'), 'of those have a factory')
