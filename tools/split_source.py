"""Split imperialism_named.c into src/<group>.c using the rules in names/groups.tsv (src/ is git-ignored, like the input).
Usage: python tools/split_source.py   (prints a function count per group)"""
import os, re, collections

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
rules = []
for ln in open(RE + 'names/groups.tsv', encoding='utf-8'):
    if ln.startswith('#') or not ln.strip():
        continue
    on, rx, grp = ln.rstrip('\n').split('\t')
    rules.append((on, re.compile(rx), grp))

# Split into blocks: each starts at a "// name @ addr" comment; text before the first is the shared preamble.
blocks, cur, pre = [], None, []
for ln in open(RE + 'imperialism_named.c', encoding='utf-8', errors='replace'):
    m = re.match(r'// (\S+) @ ([0-9a-f]{8})', ln)
    if m:
        cur = [m[1], []]
        blocks.append(cur)
    (cur[1] if cur else pre).append(ln)


def group_of(name, text):
    for on, rx, grp in rules:
        if rx.search(name if on == 'name' else text):
            return grp
    return 'unsorted'


texts = [''.join(l) for _, l in blocks]
addr = [int(re.match(r'// \S+ @ ([0-9a-f]{8})', t)[1], 16) for t in texts]
order = sorted(range(len(blocks)), key=lambda i: addr[i])
grp = {i: group_of(blocks[i][0], texts[i]) for i in range(len(blocks))}
# 0x401000-0x40c000 is the incremental-link jmp-stub region: keep it out of the real groups.
for i in range(len(blocks)):
    if grp[i] == 'unsorted' and addr[i] < 0x40c000:
        grp[i] = 'link_stubs'
# The linker lays out each .cpp contiguously, so an unsorted function between two functions of the same group
# (nearest classified neighbours by address) belongs to that group too.
known = [i for i in order if grp[i] != 'unsorted']
nxt, prv = {}, {}
last = None
for i in order:
    if grp[i] != 'unsorted':
        last = i
    prv[i] = last
last = None
for i in reversed(order):
    if grp[i] != 'unsorted':
        last = i
    nxt[i] = last
for i in order:
    if grp[i] == 'unsorted' and prv[i] is not None and nxt[i] is not None and grp[prv[i]] == grp[nxt[i]]:
        grp[i] = grp[prv[i]]

out = collections.defaultdict(list)
for i in order:
    out[grp[i]].append(texts[i])

os.makedirs(RE + 'src', exist_ok=True)
for f in os.listdir(RE + 'src'):
    if f.endswith('.c'):
        os.remove(RE + 'src/' + f)
open(RE + 'src/_preamble.c', 'w', encoding='utf-8').write(''.join(pre))
for grp, fns in sorted(out.items()):
    open(RE + 'src/%s.c' % grp, 'w', encoding='utf-8').write('// Group: %s (%d functions)\n\n' % (grp, len(fns)) + '\n'.join(fns))
    print('%-14s %5d' % (grp, len(fns)))
