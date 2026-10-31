"""Read-only: list the ASCII strings of Imperialism.exe with their virtual addresses and section, and flag the ones that look like source references.

A string is flagged when it looks like a source file name (.cpp .c .h .inl .cc), an assertion or error message, a function/class name, or a format with a
file/line. Output is TSV: va, section, flags, text. Usage: python -I tools/exe_strings.py [--all] [exe]    (default: only flagged strings)"""
import os, re, struct, sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
show_all = '--all' in sys.argv
exe = args[0] if args else 'C:/GOG Games/Imperialism/Imperialism.exe'
d = open(exe, 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec = struct.unpack_from('<H', d, pe + 6)[0]
opt = struct.unpack_from('<H', d, pe + 20)[0]
base = struct.unpack_from('<I', d, pe + 52)[0]
secs = []
for i in range(nsec):
    o = pe + 24 + opt + i * 40
    name = d[o:o + 8].rstrip(b'\0').decode()
    vs, va, rs, ro = struct.unpack_from('<IIII', d, o + 8)
    secs.append((name, base + va, vs, ro, rs))

FILE = re.compile(r'\.(cpp|cxx|cc|c|h|hpp|inl|rc|def)\b', re.I)
ASSERT = re.compile(r'assert|assertion|ASSERT|fatal|error|invalid|failure|failed|not initialized|out of range|overflow|bad |unexpected|can.?t |cannot|debug|trace', re.I)
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)?$')
PATH = re.compile(r'[A-Za-z]:\\|\\\\|/[a-z]+/')

out = []
for name, va, vs, ro, rs in secs:
    if name in ('.text',):
        continue
    chunk = d[ro:ro + rs]
    for m in re.finditer(rb'[\x20-\x7e]{5,}', chunk):
        s = m.group().decode('ascii')
        flags = []
        if FILE.search(s):
            flags.append('file')
        if PATH.search(s):
            flags.append('path')
        if ASSERT.search(s):
            flags.append('assert')
        if IDENT.match(s) and ('_' in s or re.search(r'[a-z][A-Z]', s)) and len(s) > 6:
            flags.append('ident')
        if '%' in s and re.search(r'line|file|func|%s.*%d', s, re.I):
            flags.append('fmt')
        if flags or show_all:
            out.append('0x%08x\t%s\t%s\t%s' % (va + m.start(), name, ','.join(flags), s))
print('\n'.join(out))
