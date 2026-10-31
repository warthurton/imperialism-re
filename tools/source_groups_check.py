"""Read-only: for each original source file (names/source_attribution.tsv, from tools/source_files.py), show which of our current groups (src/<group>.c) its functions were
filed under. A file whose functions are spread over several groups points at a filing guess worth fixing; a file that sits wholly in one group confirms the group.
Only functions attributed with certainty ('assert' or 'inferred') are counted, not 'boundary'. Usage: python -I tools/source_groups_check.py"""
import collections, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
group = {}
for f in glob.glob(os.path.join(ROOT, 'src', '*.c')):
    g = os.path.basename(f)[:-2]
    if g.startswith('_'):
        continue
    for m in HEAD.finditer(open(f, encoding='utf-8', errors='replace').read()):
        group[m.group(2)] = g
per = collections.defaultdict(collections.Counter)
order = []
for line in open(os.path.join(ROOT, 'names', 'source_attribution.tsv'), encoding='utf-8'):
    addr, name, fn, how, lines = line.rstrip('\n').split('\t')
    if how == 'boundary':
        continue
    if fn not in per:
        order.append(fn)
    per[fn][group.get(addr, '?')] += 1
for fn in order:
    c = per[fn]
    total = sum(c.values())
    top = ', '.join('%s %d' % kv for kv in c.most_common(4))
    print('%-30s %4d  %s' % (fn, total, top))
