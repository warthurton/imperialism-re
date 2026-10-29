"""Find statically linked library functions (MFC, C runtime) inside Imperialism.exe by byte matching.

For every code section (one per function, the libraries were built with /Gy) of a COFF static library (.lib),
bytes the linker patched (relocation targets) are masked out; the remaining bytes must match the exe's .text.

usage: python -I match_lib.py <lib> [<lib> ...]  ->  writes lib_matches.tsv (va, size, name, library, ambiguity)
"""
import struct, sys, re, json

EXE = 'C:/GOG Games/Imperialism/Imperialism.exe'
OUT = 'C:/GOG Games/Imperialism-RE/lib_matches.tsv'
MIN_FIXED = 10          # need at least this many unmasked bytes in a function to trust a match

exe = open(EXE, 'rb').read()
pe = struct.unpack_from('<I', exe, 0x3c)[0]
nsec = struct.unpack_from('<H', exe, pe + 6)[0]
opt = struct.unpack_from('<H', exe, pe + 20)[0]
base = struct.unpack_from('<I', exe, pe + 24 + 28)[0]
text = None
for i in range(nsec):
    s = exe[pe + 24 + opt + 40 * i: pe + 24 + opt + 40 * i + 40]
    if s[:8].rstrip(b'\0') == b'.text':
        vs, va, rs, rp = struct.unpack_from('<IIII', s, 8)
        text = (base + va, exe[rp:rp + min(vs, rs)])
TVA, TXT = text


def members(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'!<arch>\n'
    p = 8; longnames = b''; out = []
    while p + 60 <= len(d):
        name = d[p:p + 16].decode('latin1').strip(); size = int(d[p + 48:p + 58].decode().strip())
        body = d[p + 60:p + 60 + size]; p += 60 + size + (size & 1)
        if name == '//':
            longnames = body
        elif name in ('/', '/<ECB>/'):
            pass
        else:
            if name.startswith('/') and name[1:].isdigit():
                o = int(name[1:])
                e = min(x for x in (longnames.find(b'\0', o), longnames.find(b'\n', o), len(longnames)) if x >= 0)
                name = longnames[o:e].decode('latin1').rstrip('/')
            out.append((name.rstrip('/'), body))
    return out


def coff_functions(obj):
    """yield (name, bytes, mask list of (off,len)) for code sections of one COFF object"""
    if len(obj) < 20 or struct.unpack_from('<H', obj, 0)[0] != 0x14c:
        return
    nsecs, _, symptr, nsyms = struct.unpack_from('<HIII', obj, 2)
    strtab = symptr + 18 * nsyms
    def symname(i):
        o = symptr + 18 * i
        if obj[o:o + 4] == b'\0\0\0\0':
            so = struct.unpack_from('<I', obj, o + 4)[0]
            e = obj.index(b'\0', strtab + so)
            return obj[strtab + so:e].decode('latin1')
        return obj[o:o + 8].rstrip(b'\0').decode('latin1')
    # symbols by section
    bysec = {}
    i = 0
    while i < nsyms:
        o = symptr + 18 * i
        val, secno, typ, sc, aux = struct.unpack_from('<IhHBB', obj, o + 8)
        if secno > 0 and sc in (2, 3) and typ != 0 or (secno > 0 and sc == 2):
            bysec.setdefault(secno, []).append((val, sc, symname(i)))
        i += 1 + aux
    for si in range(nsecs):
        h = 20 + 40 * si
        name = obj[h:h + 8].rstrip(b'\0').decode('latin1')
        vsz, vaddr, rsz, rptr, relptr, lnptr, nrel, nln, chars = struct.unpack_from('<IIIIIIHHI', obj, h + 8)
        if not (chars & 0x20) or rsz == 0:
            continue
        data = obj[rptr:rptr + rsz]
        mask = []
        for r in range(nrel):
            ro = relptr + 10 * r
            va, sym, typ = struct.unpack_from('<IIH', obj, ro)
            if typ in (6, 7, 0x14):           # DIR32, DIR32NB, REL32
                mask.append((va, 4))
            elif typ in (0x0a, 0x0b):         # SECTION, SECREL (2/4 bytes)
                mask.append((va, 4 if typ == 0x0b else 2))
        cands = sorted(bysec.get(si + 1, []), key=lambda t: (t[0] != 0, t[1] != 2))
        nm = cands[0][2] if cands else '%s#%d' % (name, si)
        yield nm, data, mask


def pattern(data, mask):
    m = bytearray(b'\xff' * len(data))
    for off, ln in mask:
        for k in range(ln):
            if off + k < len(m): m[off + k] = 0
    # strip trailing alignment padding
    end = len(data)
    while end > 0 and data[end - 1] in (0xCC, 0x90) and m[end - 1] == 0xff: end -= 1
    return data[:end], bytes(m[:end])


def longest_run(m, limit=160):
    best = (0, 0); s = None
    for i in range(min(len(m), limit) + 1):
        ok = i < min(len(m), limit) and m[i] == 0xff
        if ok and s is None: s = i
        if not ok and s is not None:
            if i - s > best[1] - best[0]: best = (s, i)
            s = None
    return best


results = {}   # va -> list of (name, size, lib)
tried = 0
for lib in sys.argv[1:]:
    short = lib.replace('\\', '/').split('/')[-1]
    for oname, obj in members(lib):
        for nm, data, mask in coff_functions(obj):
            pat, msk = pattern(data, mask)
            if sum(1 for b_ in msk if b_ == 0xff) < MIN_FIXED:
                continue
            tried += 1
            a, b_ = longest_run(msk)
            if b_ - a < 5:
                continue
            lit = pat[a:b_]
            pos = TXT.find(lit); hits = []
            while pos >= 0:
                start = pos - a
                if start >= 0 and start + len(pat) <= len(TXT):
                    cand = TXT[start:start + len(pat)]
                    if all(cand[i] == pat[i] for i in range(len(pat)) if msk[i]):
                        hits.append(start)
                pos = TXT.find(lit, pos + 1)
            for h in hits:
                results.setdefault(TVA + h, []).append((nm, len(pat), short))

with open(OUT, 'w') as f:
    f.write('\t'.join(['va', 'size', 'name', 'lib', 'distinct_names', 'all_names']) + '\n')
    for va in sorted(results):
        c = results[va]
        c.sort(key=lambda t: -t[1])
        names_ = sorted({x[0] for x in c})
        f.write('\t'.join(['%08x' % va, str(c[0][1]), c[0][0], c[0][2], str(len(names_)), ';'.join(names_)[:300]]) + '\n')
print('functions tried', tried, '-> distinct exe addresses matched', len(results),
      '(unique name:', sum(1 for v in results.values() if len({x[0] for x in v}) == 1), ')')
