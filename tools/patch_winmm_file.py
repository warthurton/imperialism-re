"""Write the three buffer-recycle race fixes into a copy of GOG's winmm.dll on disk.

Same replacement code as shim/winmm_cave.h (atomic claim of the slot before unprepare/free), minus the
debug counters, so it fits inside the original blocks. Only absolute operands in the new code are the
slot table and the HWAVEOUT global; the DLL's relocation entries inside the patched blocks are
rewritten to match, so the file is still correct if Windows loads it away from 0x6AB40000.

usage: python -I patch_winmm_file.py <original winmm.dll> <output winmm.dll>
"""
import re, struct, sys, hashlib

src, dst = sys.argv[1], sys.argv[2]
hdr = open('C:/GOG Games/Imperialism-RE/shim/winmm_sites.h').read()


def const(name):
    return int(re.search(r'#define\s+' + name + r'\s+(0x[0-9A-Fa-f]+)', hdr)[1], 16)


BASE = const('WINMM_BASE'); TS = const('WINMM_TIMESTAMP'); SIZE = const('WINMM_SIZEOFIMAGE')
TABLE = const('WINMM_SLOT_TABLE'); HWO = const('WINMM_HWO')
UNPREP = const('WINMM_UNPREP_THUNK'); FREE = const('WINMM_FREE_THUNK')
sites = []
for n in (1, 2, 3):
    va = const(f'WINMM_S{n}_VA'); resume = const(f'WINMM_S{n}_RESUME')
    m = re.search(r'WINMM_S%d_ORIG\[\d+\] = \{(.*?)\};' % n, hdr, re.S)
    orig = bytes(int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2})', m[1]))
    sites.append((va, resume, orig))

b = bytearray(open(src, 'rb').read())
print('input sha256', hashlib.sha256(b).hexdigest())
pe = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, pe + 6)[0]
opt = struct.unpack_from('<H', b, pe + 20)[0]
assert struct.unpack_from('<I', b, pe + 8)[0] == TS, 'timestamp differs: not the analysed winmm.dll'
assert struct.unpack_from('<I', b, pe + 24 + 56)[0] == SIZE, 'SizeOfImage differs'
assert struct.unpack_from('<I', b, pe + 24 + 28)[0] == BASE, 'ImageBase differs'
secs = []
for i in range(nsec):
    s = b[pe + 24 + opt + 40 * i: pe + 24 + opt + 40 * i + 40]
    vs, va, rs, rp = struct.unpack_from('<IIII', s, 8)
    secs.append((s[:8].rstrip(b'\0').decode(), va, vs, rp, rs))


def off(va):
    rva = va - BASE
    for nm, v, vs, rp, rs in secs:
        if v <= rva < v + max(vs, rs):
            return rp + rva - v
    raise ValueError(hex(va))


def build(va, resume):
    """Returns (code bytes, offsets of absolute operands inside code)."""
    out = bytearray(); abs_off = []
    def emit(*bs): out.extend(bs)
    def u32(v): out.extend(struct.pack('<I', v & 0xffffffff))
    def rel(target):
        u32(target - (va + len(out) + 4))
    emit(0x33, 0xC9)                         # xor ecx, ecx
    emit(0xF0, 0x0F, 0xB1, 0x0C, 0x9D)       # lock cmpxchg [4*ebx+table], ecx   (eax = expected p)
    abs_off.append(len(out)); u32(TABLE)
    emit(0x0F, 0x85); jne = len(out); u32(0)  # jne skip
    emit(0x52, 0x50, 0x6A, 0x20, 0x50)       # push edx; push eax; push 0x20; push eax
    emit(0xFF, 0x35); abs_off.append(len(out)); u32(HWO)  # push dword [hwo]
    emit(0xE8); rel(UNPREP)                  # call waveOutUnprepareHeader thunk (stdcall)
    emit(0x8B, 0x04, 0x24)                   # mov eax, [esp]
    emit(0xFF, 0x30)                         # push [eax]   (lpData)
    emit(0xE8); rel(FREE)
    emit(0x83, 0xC4, 0x04)
    emit(0xFF, 0x34, 0x24)                   # push [esp]   (the header)
    emit(0xE8); rel(FREE)
    emit(0x83, 0xC4, 0x04)
    emit(0x83, 0xC4, 0x04)                   # drop saved p
    emit(0x5A)                               # pop edx
    emit(0xE9); rel(resume)
    out[jne:jne + 4] = struct.pack('<i', len(out) - (jne + 4))
    emit(0xE9); rel(resume)                  # skip: another thread owns the slot
    return bytes(out), abs_off


# relocation table
reloc_rva, reloc_sz = struct.unpack_from('<II', b, pe + 24 + 96 + 5 * 8)
ro = off(BASE + reloc_rva)
entries = []   # (file offset of the 16-bit entry, absolute VA it fixes, type)
p = ro
while p < ro + reloc_sz:
    page, bs = struct.unpack_from('<II', b, p)
    if bs == 0: break
    for i in range((bs - 8) // 2):
        e = struct.unpack_from('<H', b, p + 8 + 2 * i)[0]
        entries.append((p + 8 + 2 * i, BASE + page + (e & 0xfff), e >> 12, page))
    p += bs

for va, resume, orig in sites:
    o = off(va)
    assert bytes(b[o:o + len(orig)]) == orig, f'site {va:#x}: bytes differ from the analysed build'
    code, abs_off = build(va, resume)
    assert len(code) <= len(orig), (len(code), len(orig))
    b[o:o + len(orig)] = code + b'\xCC' * (len(orig) - len(code))
    # relocs: entries inside this block: retarget the first len(abs_off) to the new operands, neutralise the rest
    mine = [e for e in entries if e[2] == 3 and va <= e[1] < va + len(orig)]
    assert len(mine) >= len(abs_off), 'not enough relocation slots to reuse'
    for k, (eo, eva, et, page) in enumerate(mine):
        if k < len(abs_off):
            newva = va + abs_off[k]
            assert (newva - BASE) & ~0xfff == page, 'operand moved to another reloc page'
            struct.pack_into('<H', b, eo, (3 << 12) | ((newva - BASE) & 0xfff))
        else:
            struct.pack_into('<H', b, eo, 0)     # IMAGE_REL_BASED_ABSOLUTE = padding, ignored
    print(f'site {va:#x}: {len(code)} bytes of code in a {len(orig)}-byte block, {len(mine)} relocs -> {len(abs_off)} kept')

# verify: every 4-byte value that looks like an absolute .bss address inside the patched blocks has a reloc, and vice versa
live = set()
p = ro
while p < ro + reloc_sz:
    page, bs = struct.unpack_from('<II', b, p)
    if bs == 0: break
    for i in range((bs - 8) // 2):
        e = struct.unpack_from('<H', b, p + 8 + 2 * i)[0]
        if e >> 12 == 3: live.add(BASE + page + (e & 0xfff))
    p += bs
for va, resume, orig in sites:
    o = off(va)
    for k in range(len(orig) - 3):
        v = struct.unpack_from('<I', b, o + k)[0]
        if v in (TABLE, HWO): assert va + k in live, f'abs operand at {va + k:#x} has no reloc'
    for r in live:
        if va <= r < va + len(orig):
            assert struct.unpack_from('<I', b, off(r))[0] in (TABLE, HWO), f'reloc at {r:#x} points at non-address bytes'
open(dst, 'wb').write(b)
print('output sha256', hashlib.sha256(b).hexdigest(), '->', dst)
