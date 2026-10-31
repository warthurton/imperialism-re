"""Audit the last-resort address-range rows in names/groups.tsv: for each laddr range, how many functions placed there have call-graph neighbours (callers + callees, library groups ignored) mostly in the same group.
Run after tools/split_source.py, from the repo root. "disagree" is a prompt to look, not proof: UI code is often called from sim code."""
import re, collections, glob, os
grp = {}; txt = {}
for f in glob.glob('src/*.c'):
    g = os.path.basename(f)[:-2]
    if g.startswith('_'):
        continue
    t = open(f, encoding='utf-8', errors='replace').read()
    for b in re.split(r'\n(?=// [A-Za-z_0-9]+ @ [0-9a-f]{8})', t):
        m = re.match(r'// (\S+) @ ([0-9a-f]{8})', b)
        if m:
            grp[m[2]] = g; txt[m[2]] = b
calls = collections.defaultdict(set)
for a, b in txt.items():
    for m in re.finditer(r'(?:FUN_|thunk_FUN_)([0-9a-f]{8})', b):
        if m[1] != a:
            calls[a].add(m[1])
callers = collections.defaultdict(set)
for a, cs in calls.items():
    for c in cs:
        callers[c].add(a)
SKIP = ('link_stubs', 'crt', 'mfc', 'static_init', 'dtor_wrappers')
rows = []
for line in open('names/groups.tsv', encoding='utf-8'):
    p = line.rstrip('\r\n').split('\t')
    if p[0] == 'laddr':
        lo, hi = (int(x, 16) for x in p[1].split('-'))
        rows.append((lo, hi, p[2]))
bad = collections.defaultdict(list); tot = collections.Counter(); agree = collections.Counter()
for a, g in grp.items():
    for lo, hi, rg in rows:
        if lo <= int(a, 16) <= hi and g == rg:
            nb = collections.Counter(grp.get(c, '?') for c in callers[a] | calls[a])
            for k in SKIP + ('?',):
                nb.pop(k, None)
            tot[(lo, rg)] += 1
            if not nb:
                continue
            if nb.get(g, 0) * 2 >= sum(nb.values()):
                agree[(lo, rg)] += 1
            else:
                bad[(lo, rg)].append((a, dict(nb.most_common(2))))
for k in sorted(tot):
    print('%08x %-12s n=%3d agree=%3d disagree=%3d' % (k[0], k[1], tot[k], agree[k], len(bad[k])))
    for a, nb in bad[k][:4]:
        print('     ', a, nb)
