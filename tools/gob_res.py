import struct, sys

def load(path):
    b = open(path, 'rb').read()
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    n = struct.unpack_from('<H', b, pe + 6)[0]
    opt = struct.unpack_from('<H', b, pe + 20)[0]
    sec = pe + 24 + opt
    secs = []
    for i in range(n):
        s = b[sec + 40 * i: sec + 40 * i + 40]
        nm = s[:8].rstrip(b'\0').decode()
        vs, va, rs, rp = struct.unpack_from('<IIII', s, 8)
        secs.append((nm, va, vs, rp, rs))
    rva_rsrc = struct.unpack_from('<I', b, pe + 24 + 96 + 16)[0]  # data dir 2 (resource)
    return b, secs, rva_rsrc

def rva2off(secs, rva):
    for nm, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + rva - va

def walk(b, secs, rva_rsrc):
    base = rva2off(secs, rva_rsrc)
    out = []
    def name(off):
        o = base + (off & 0x7fffffff)
        l = struct.unpack_from('<H', b, o)[0]
        return b[o + 2: o + 2 + 2 * l].decode('utf-16le')
    def entries(off):
        o = base + off
        nn, ni = struct.unpack_from('<HH', b, o + 12)
        res = []
        for i in range(nn + ni):
            nid, d = struct.unpack_from('<II', b, o + 16 + 8 * i)
            res.append((name(nid) if nid & 0x80000000 else nid, d))
        return res
    for t, d in entries(0):
        for nme, d2 in entries(d & 0x7fffffff):
            for lang, d3 in entries(d2 & 0x7fffffff):
                o = base + d3
                rva, size = struct.unpack_from('<II', b, o)
                out.append((t, nme, lang, rva2off(secs, rva), size))
    return out

if __name__ == '__main__':
    b, secs, r = load(sys.argv[1])
    res = walk(b, secs, r)
    from collections import Counter
    print(len(res), 'resources; by type:', Counter(x[0] for x in res).most_common(20))
    for x in res[:12]:
        print(x)
