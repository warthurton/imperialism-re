"""Read-only: print the exception, faulting address, module and the crashing thread's stack words from a Windows minidump (WER LocalDumps, full dump).
Usage: python -I dumpinfo.py <dump file> [stack_words]      (default 48)
Only parses the MINIDUMP directory: ExceptionStream (6), ModuleListStream (4), ThreadListStream (3), Memory64ListStream (9). No symbols: addresses in
Imperialism.exe (base 0x400000) can be looked up in the decompile (names/names.tsv, `python -I tools/find_calls.py`)."""
import struct, sys

f = open(sys.argv[1], 'rb'); data = f.read(); words = int(sys.argv[2]) if len(sys.argv) > 2 else 48
assert data[:4] == b'MDMP', 'not a minidump'
nstreams, dirrva = struct.unpack_from('<II', data, 8)[0:2]
streams = {}
for i in range(nstreams):
    t, size, rva = struct.unpack_from('<III', data, dirrva + i * 12)
    streams[t] = (size, rva)
mods = []
if 4 in streams:
    n, = struct.unpack_from('<I', data, streams[4][1])
    for i in range(n):
        base, size = struct.unpack_from('<QI', data, streams[4][1] + 4 + i * 108)
        nrva, = struct.unpack_from('<I', data, streams[4][1] + 4 + i * 108 + 20)
        ln, = struct.unpack_from('<I', data, nrva)
        mods.append((base, size, data[nrva + 4:nrva + 4 + ln].decode('utf-16le').split('\\')[-1]))
def where(a):
    for b, s, n in mods:
        if b <= a < b + s: return '%s+0x%x' % (n, a - b)
    return '?'
tid = None
if 6 in streams:
    r = streams[6][1]
    tid, = struct.unpack_from('<I', data, r)
    code, flags, rec, addr, nparam = struct.unpack_from('<IIQQI', data, r + 8)
    params = struct.unpack_from('<15Q', data, r + 8 + 32)
    print('exception 0x%08x at 0x%x (%s), thread %d, parameters %s' % (code, addr, where(addr), tid, [hex(p) for p in params[:nparam]]))
else:
    print('no exception stream')
# memory ranges
mem = []
if 9 in streams:
    n, base_rva = struct.unpack_from('<QQ', data, streams[9][1])
    off = base_rva
    for i in range(n):
        start, ln = struct.unpack_from('<QQ', data, streams[9][1] + 16 + i * 16)
        mem.append((start, ln, off)); off += ln
def readmem(a, n):
    for s, ln, o in mem:
        if s <= a and a + n <= s + ln: return data[o + (a - s):o + (a - s) + n]
    return None
if 6 in streams:
    # the exception stream carries the context AT THE FAULT (the thread list's context is the reporting thread's)
    ctx_size, ctx_rva = struct.unpack_from('<II', data, streams[6][1] + 8 + 152)
    for _ in [0]:
        for _ in [0]:
            c = ctx_rva  # x86 CONTEXT: Eip at 0xb8, Esp at 0xc4, Ebp 0xb4
            eip, = struct.unpack_from('<I', data, c + 0xb8); esp, = struct.unpack_from('<I', data, c + 0xc4); ebp, = struct.unpack_from('<I', data, c + 0xb4)
            regs = {n_: struct.unpack_from('<I', data, c + o)[0] for n_, o in (('eax', 0xb0), ('ecx', 0xac), ('edx', 0xa8), ('ebx', 0xa4), ('esi', 0xa0), ('edi', 0x9c))}
            print('crashing thread context: eip=%08x (%s) esp=%08x ebp=%08x' % (eip, where(eip), esp, ebp))
            print('  ' + ' '.join('%s=%08x' % kv for kv in regs.items()))
            raw = readmem(esp, words * 4)
            if raw:
                print('stack words that point into a module (likely return addresses):')
                for k in range(words):
                    v, = struct.unpack_from('<I', raw, k * 4)
                    w = where(v)
                    if w != '?': print('  esp+0x%02x  %08x  %s' % (k * 4, v, w))
for b, s, n in mods[:6]: print('module %-24s base %08x size %x' % (n, b, s))
