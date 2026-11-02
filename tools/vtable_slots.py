"""Read-only: print entries of a vtable straight from Imperialism.exe (no running game needed).
Usage: python -I vtable_slots.py <vtable VA hex> <byte offset hex> [<byte offset hex> ...]      e.g. vtable_slots.py 0x6587e0 0x68 0x124 0x128
Each slot prints the function address it holds. Look the address up in names/names.tsv or the decompile (`// NAME @ ADDR`)."""
import struct, sys

exe = open('C:/GOG Games/Imperialism/Imperialism.exe', 'rb').read()
pe = struct.unpack_from('<I', exe, 0x3c)[0]
nsec = struct.unpack_from('<H', exe, pe + 6)[0]; optsz = struct.unpack_from('<H', exe, pe + 20)[0]
base = struct.unpack_from('<I', exe, pe + 24 + 28)[0]
secs = []
for i in range(nsec):
    o = pe + 24 + optsz + i * 40
    vsz, va, rsz, raw = struct.unpack_from('<IIII', exe, o + 8)
    secs.append((base + va, vsz, raw))


def u32_at(va):
    for s, vsz, raw in secs:
        if s <= va < s + vsz:
            return struct.unpack_from('<I', exe, raw + va - s)[0]
    return None


def byte_at(va):
    for s, vsz, raw in secs:
        if s <= va < s + vsz:
            return exe[raw + va - s: raw + va - s + 5]
    return b''


def follow(v):
    """the vtable usually holds a 5-byte `jmp rel32` thunk in the 0x40xxxx stub area: return the real target"""
    b = byte_at(v)
    if len(b) == 5 and b[0] == 0xE9:
        return (v + 5 + struct.unpack('<i', b[1:])[0]) & 0xffffffff
    return v


vt = int(sys.argv[1], 16)
for off in sys.argv[2:]:
    o = int(off, 16)
    v = u32_at(vt + o)
    print('slot +0x%x (%d) = %s -> %s' % (o, o // 4, '0x%08x' % v if v else None, '0x%08x' % follow(v) if v else None))
