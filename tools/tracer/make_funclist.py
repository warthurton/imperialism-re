"""Write the list of function entry points for tools/tracer/trace_calls.c from the decompile groups in src/ (run tools/split_source.py first).

Library code (crt, mfc, link stubs, static initializers, destructor wrappers, the framework group) and the parked multiplayer groups are left out; the stub region below 0x410000
only holds jump thunks. Usage: python -I tools/tracer/make_funclist.py [out.txt]      (default results/funclist.txt, git-ignored)
Each line: address, name, group."""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKIP = ('crt', 'mfc', 'link_stubs', 'static_init', 'dtor_wrappers', 'framework', 'multiplayer', 'directplay')
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'results', 'funclist.txt')
rows = []
for f in glob.glob(os.path.join(ROOT, 'src', '*.c')):
    g = os.path.basename(f)[:-2]
    if g.startswith('_') or g in SKIP:
        continue
    for m in HEAD.finditer(open(f, encoding='utf-8', errors='replace').read()):
        a = int(m.group(2), 16)
        if a >= 0x410000:
            rows.append((a, m.group(1), g))
rows.sort()
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for a, n, g in rows:
        fh.write('%08x %s %s\n' % (a, n, g))
print('%d functions -> %s' % (len(rows), out))
