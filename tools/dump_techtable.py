"""Read-only: dump the tech-release range tables from Imperialism.exe (no game needed).
FUN_005af330 draws, for each scheduled tech slot, a random turn in [lo*4, hi*4] from short pairs at 0x66ab9a..0x66ac0e (years x 4 seasons).
Usage: python -I tools/dump_techtable.py [exe path]"""
import struct, sys
exe = sys.argv[1] if len(sys.argv) > 1 else 'C:/GOG Games/Imperialism/Imperialism.exe'
d = open(exe, 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec = struct.unpack_from('<H', d, pe + 6)[0]; opt = struct.unpack_from('<H', d, pe + 20)[0]
base = struct.unpack_from('<I', d, pe + 52)[0]
secs = []
for i in range(nsec):
    o = pe + 24 + opt + i * 40
    vs, va, rs, ro = struct.unpack_from('<IIII', d, o + 8)
    secs.append((base + va, vs, ro, rs))
def rd(va, n):
    for s, vs, ro, rs in secs:
        if s <= va < s + max(vs, rs):
            return d[ro + va - s: ro + va - s + n]
    raise ValueError(hex(va))
def shorts(va, n): return list(struct.unpack('<%dh' % n, rd(va, 2 * n)))
if __name__ == '__main__':
    print('pairs at 0x66ab9a (lo, hi):')
    v = shorts(0x66ab9a, (0x66ac0e - 0x66ab9a) // 2 + 2)
    for i in range(0, len(v) - 1, 2):
        print(hex(0x66ab9a + 2 * i), v[i], v[i + 1])
    print('DAT_0066aaf4 (ints, cost?):', list(struct.unpack('<29i', rd(0x66aaf4, 116))))
