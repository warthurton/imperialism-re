import struct, json, re, csv

RE = 'C:/GOG Games/Imperialism-RE/'
b = open('C:/GOG Games/Imperialism/Imperialism.exe', 'rb').read()
d = json.load(open(RE + 'pe_secs.json'))
base = d['base']; secs = d['secs']
text = [s for s in secs if s[0] == '.text'][0]
tlo = base + text[1]; thi = tlo + text[2]


def va2off(v):
    for nm, rv, vs, rp, rs in secs:
        if base + rv <= v < base + rv + max(vs, rs):
            return rp + v - base - rv


def res(v):  # follow an incremental-link jmp stub
    o = va2off(v)
    return v + 5 + struct.unpack_from('<i', b, o + 1)[0] if b[o] == 0xE9 else v


FILES = ('imperialism_decomp.c', 'imperialism_decomp_extra.c')
bodies = {}
for fn in FILES:
    cur = None; buf = []
    for ln in open(RE + fn, encoding='utf-8', errors='replace'):
        m = re.match(r'// (?:FAILED )?(\S+) @ ([0-9a-f]{8})', ln)
        if m:
            if cur: bodies[cur] = ''.join(buf)
            cur = int(m[2], 16); buf = []
        else:
            buf.append(ln)
    if cur: bodies[cur] = ''.join(buf)

rows = list(csv.reader(open(RE + 'classes.tsv'), delimiter='\t'))[1:]
cls = {r[0]: dict(base=r[4], real=int(r[5], 16) if r[5] != '-' else 0) for r in rows}

vt = {}
for n, c in cls.items():
    body = bodies.get(c['real'], '')
    m = re.search(r'= &PTR_\w*?_([0-9a-f]{8});', body)
    if not m:   # constructor not inlined into the factory: look inside the functions it calls
        for cm in re.finditer(r'\b(?:thunk_)?FUN_([0-9a-f]{8})\(', body):
            callee = res(int(cm[1], 16))
            m = re.search(r'= &PTR_\w*?_([0-9a-f]{8});', bodies.get(callee, ''))
            if m: break
    if m: vt[n] = int(m[1], 16)
print(len(vt), 'classes with a vtable found of', len(cls))


def depth(n):
    k = 0
    while n in cls and cls[n]['base'] in cls and k < 50:
        n = cls[n]['base']; k += 1
    return k


ren = {}; vtnames = {}
starts = sorted(set(vt.values()))
for n in sorted(vt, key=depth):
    o = va2off(vt[n]); i = 0
    vtnames[vt[n]] = n + '_vtable'
    nxt = min([s for s in starts if s > vt[n]] + [1 << 40])
    while vt[n] + 4 * i < nxt:
        v = struct.unpack_from('<I', b, o + 4 * i)[0]
        if not (tlo <= v < thi): break
        r = res(v)
        ren.setdefault(r, f'{n}_vf{i}')
        i += 1
for n, c in cls.items():
    if c['real']: ren.setdefault(c['real'], n + '_Create')
import os
if os.path.exists(RE + 'lib_names.json'):      # MFC / C runtime functions matched against the original static libs
    lib = json.load(open(RE + 'lib_names.json'))['funcs']
    for a, n in lib.items():
        ren[int(a, 16)] = n
    print(len(lib), 'library names applied')
print(len(ren), 'functions named (before hand-assigned names)')

# Hand-assigned names (names/names.tsv): highest priority. addr column is a hex address or an existing generated
# name such as TTradeMgr_vf11. kind = func | global. Every row carries a confidence and the evidence.
inv = {}
for a_, n_ in ren.items(): inv.setdefault(n_, a_)
hand = {}; hand_globals = {}; notes = {}
if os.path.exists(RE + 'names/names.tsv'):
    for ln in open(RE + 'names/names.tsv', encoding='utf-8'):
        if ln.startswith('#') or not ln.strip() or ln.startswith('addr\t'): continue
        addr, name, kind, conf, note = (ln.rstrip('\n').split('\t') + ['', '', '', '', ''])[:5]
        if kind == 'global':
            hand_globals[addr] = (name, conf, note)
        else:
            a_ = int(addr, 16) if re.fullmatch(r'[0-9a-fA-F]{6,8}', addr) else inv.get(addr)
            if a_ is None: print('names.tsv: cannot resolve', addr); continue
            ren[a_] = name; hand[a_] = name; notes[a_] = (conf, note)
print(len(hand), 'hand-assigned function names,', len(hand_globals), 'globals')
json.dump({'funcs': {f'{k:08x}': v for k, v in ren.items()},
           'vtables': {f'{k:08x}': v for k, v in vtnames.items()}}, open(RE + 'renames.json', 'w'), indent=0)

cnt = 0


def f(m):
    global cnt
    a = int(m[2], 16)
    if a in ren:
        cnt += 1
        return ren[a]
    return m[0]


with open(RE + 'imperialism_named.c', 'w', encoding='utf-8') as out:
    for fn in FILES:
        t = open(RE + fn, encoding='utf-8', errors='replace').read()
        t = re.sub(r'\b(thunk_FUN_|FUN_)([0-9a-f]{8})\b', f, t)
        t = re.sub(r'\bPTR_LAB_([0-9a-f]{8})\b', lambda m: vtnames.get(int(m[1], 16), m[0]), t)
        for g, (gn, gc, gnote) in hand_globals.items():
            t = re.sub(r'\b(?:PTR_)?DAT_' + g + r'\b', gn, t)
        def hdr(m):   # annotate hand-named function headers with confidence and evidence
            a_ = int(m[2], 16)
            return m[0] + ('  [%s] %s' % notes[a_]) if a_ in notes else m[0]
        t = re.sub(r'^// (\S+) @ ([0-9a-f]{8})(?=\r?$)', hdr, t, flags=re.M)
        out.write(t)
print('replacements', cnt)
