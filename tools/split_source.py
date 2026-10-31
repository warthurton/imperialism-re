"""Split imperialism_named.c into src/<group>.c using the rules in names/groups.tsv (src/ is git-ignored, like the input).
Usage: python tools/split_source.py   (prints a function count per group)"""
import os, re, sys, collections

RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdk_annotate import annotate_dp
rules = []
addr_rules = []
late_addr = []                             # "laddr" rows: address ranges tried only on still-unsorted functions
late_rules = []                            # "late" rows: body regex tried only on functions every other pass left unsorted
for ln in open(RE + 'names/groups.tsv', encoding='utf-8'):
    if ln.startswith('#') or not ln.strip():
        continue
    on, rx, grp = ln.rstrip('\r\n').split('\t')
    if on == 'laddr':
        lo, hi = (int(x, 16) for x in rx.split('-'))
        late_addr.append((lo, hi, grp))
        continue
    if on == 'addr':                       # explicit address range "start-end" (hex), e.g. SDK wrapper code
        lo, hi = (int(x, 16) for x in rx.split('-'))
        addr_rules.append((lo, hi, grp))
        continue
    (late_rules if on == 'late' else rules).append((on, re.compile(rx), grp))

# Split into blocks: each starts at a "// name @ addr" comment; text before the first is the shared preamble.
blocks, cur, pre = [], None, []
for ln in open(RE + 'imperialism_named.c', encoding='utf-8', errors='replace'):
    m = re.match(r'// (\S+) @ ([0-9a-f]{8})', ln)
    if m:
        cur = [m[1], []]
        blocks.append(cur)
    (cur[1] if cur else pre).append(ln)


CLASS_GETTER = re.compile(r'\n\{\s*return &PTR_s_(\w+?)_[0-9a-f]{8};\s*\}')   # MFC GetThisClass()/GetRuntimeClass() stubs


def group_of(name, text):
    for on, rx, grp in rules:
        if rx.search(name if on == 'name' else text):
            return grp
    m = CLASS_GETTER.search(text)
    if m:                                  # belongs wherever the class it describes belongs
        g = group_of(m[1] + '_x', '')
        return 'mfc' if m[1].startswith('C') and g == 'unsorted' else g
    return 'unsorted'


texts = [''.join(l) for _, l in blocks]
addr = [int(re.match(r'// \S+ @ ([0-9a-f]{8})', t)[1], 16) for t in texts]
order = sorted(range(len(blocks)), key=lambda i: addr[i])
grp = {i: group_of(blocks[i][0], texts[i]) for i in range(len(blocks))}
for i in range(len(blocks)):               # explicit address ranges win over name rules
    for lo, hi, g in addr_rules:
        if lo <= addr[i] <= hi and addr[i] >= 0x410000:
            grp[i] = g
# 0x401000-0x40c000 is the incremental-link jmp-stub region: keep it out of the real groups.
for i in range(len(blocks)):
    if grp[i] == 'unsorted' and addr[i] < 0x40c000:
        grp[i] = 'link_stubs'
# C++ global constructors: no params, only stores of constants (or __ftol of a constant) into globals, optionally an atexit.
INIT_STMT = re.compile(r'(\w+(\._\d_\d_)? = (0|0x[0-9a-f]+|-?\d+(\.\d+)?f?|__ftol\(\)|&\w+);|crt_atexit\(&LAB_[0-9a-f]{8}\);)')


def is_static_init(text):
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith(('//', '/*'))]
    if len(lines) < 4 or not re.match(r'void FUN_[0-9a-f]{8}\(void\)$', lines[0]) or lines[1] != '{' or lines[-2:] != ['return;', '}']:
        return False
    return all(INIT_STMT.fullmatch(l) for l in lines[2:-2])


# The linker lays out each .cpp contiguously, so an unsorted function between two functions of the same group
# (nearest classified neighbours by address) belongs to that group too.
def sandwich():
    nxt, prv = {}, {}
    last = None
    for i in order:
        if grp[i] not in ('unsorted', 'link_stubs'):
            last = i
        prv[i] = last
    last = None
    for i in reversed(order):
        if grp[i] not in ('unsorted', 'link_stubs'):
            last = i
        nxt[i] = last
    for i in order:
        if grp[i] == 'unsorted' and prv[i] is not None and nxt[i] is not None and grp[prv[i]] == grp[nxt[i]]:
            grp[i] = grp[prv[i]]



sandwich()

# Original source files: the game's assert strings name the .cpp a function came from (D:\Ambit\<file>.cpp). Each file is one
# contiguous address range, so an unsorted function inside exactly one file's range (first..last assert) joins that file's group.
file_group = {}
for ln in open(RE + 'names/source_files.tsv', encoding='utf-8'):
    if ln.startswith('#') or not ln.strip():
        continue
    f, g = ln.rstrip('\r\n').split('\t')
    file_group[f] = g
anchors = collections.defaultdict(list)
for i in range(len(blocks)):
    if addr[i] < 0x410000:
        continue                      # stub region holds copies of constructors etc., not the real file layout
    for m in re.finditer(r's_D__Ambit_(\w+?)_cpp_', texts[i]):
        anchors[m[1]].append(addr[i])
ranges = {f: (min(a), max(a)) for f, a in anchors.items() if f in file_group}
for i in order:
    if grp[i] == 'unsorted':
        inside = {file_group[f] for f, (lo, hi) in ranges.items() if lo <= addr[i] <= hi}
        if len(inside) == 1:
            grp[i] = inside.pop()

# Call graph: an unsorted function whose classified callers all share one group joins it (repeat until stable).
by_addr = {addr[i]: i for i in range(len(blocks))}
callers = collections.defaultdict(set)
for i in range(len(blocks)):
    for m in re.finditer(r'(?:FUN_|thunk_FUN_)([0-9a-f]{8})', texts[i]):
        j = by_addr.get(int(m[1], 16))
        if j is not None and j != i:
            callers[j].add(i)
changed = True
while changed:
    changed = False
    for i in order:
        if grp[i] in ('unsorted',) and callers[i]:
            gs = {grp[c] for c in callers[i] if grp[c] not in ('unsorted', 'link_stubs')}
            if len(gs) == 1:
                grp[i] = gs.pop()
                changed = True
                continue
            votes = collections.Counter(grp[c] for c in callers[i] if grp[c] not in ('unsorted', 'link_stubs', 'mfc', 'crt'))
            if votes:                      # library callers don't count; a 70% majority of the rest decides
                g, n = votes.most_common(1)[0]
                if n * 10 >= sum(votes.values()) * 7:
                    grp[i] = g
                    changed = True
    sandwich()

# Callees: an unsorted function whose calls mostly land in one group (ignoring library code and stubs) joins that group.
callees = collections.defaultdict(list)
for j, cs in callers.items():
    for c in cs:
        callees[c].append(j)
changed = True
while changed:
    changed = False
    for i in order:
        if grp[i] != 'unsorted' or not callees[i]:
            continue
        gs = collections.Counter(grp[j] for j in callees[i] if grp[j] not in ('unsorted', 'link_stubs', 'mfc', 'crt'))
        tot = sum(gs.values())
        if tot >= 2:
            g, n = gs.most_common(1)[0]
            if n * 10 >= tot * 7:
                grp[i] = g
                changed = True

for i in order:
    if grp[i] == 'unsorted':
        for lo, hi, g in late_addr:
            if lo <= addr[i] <= hi:
                grp[i] = g
        for _, rx, g in (late_rules if grp[i] == 'unsorted' else ()):
            if rx.search(texts[i]):
                grp[i] = g
                break

# Weakest evidence, tried last and repeated until stable: a plurality (>= half) of the classified callers, or, for a function
# nobody classified calls, the single group its callees live in (a leaf helper of that group's code).
LIB = ('unsorted', 'link_stubs', 'mfc', 'crt', 'static_init')
changed = True
while changed:
    changed = False
    for i in order:
        if grp[i] != 'unsorted':
            continue
        votes = collections.Counter(grp[c] for c in callers[i] if grp[c] not in LIB)
        if votes:
            g, n = votes.most_common(1)[0]
            if n * 2 >= sum(votes.values()):
                grp[i] = g
                changed = True
            continue
        votes = collections.Counter(grp[j] for j in callees[i] if grp[j] not in LIB)
        if len(votes) == 1:
            grp[i] = next(iter(votes))
            changed = True

# Applied last so these tiny functions still act as neighbours for the passes above, then split out of whatever group absorbed them.
for i in range(len(blocks)):
    if grp[i] not in ('link_stubs', 'mfc', 'crt', 'directplay') and is_static_init(texts[i]):
        grp[i] = 'static_init'

out = collections.defaultdict(list)
for i in order:
    out[grp[i]].append(annotate_dp(texts[i]) if grp[i] == 'directplay' else texts[i])

os.makedirs(RE + 'src', exist_ok=True)
for f in os.listdir(RE + 'src'):
    if f.endswith('.c'):
        os.remove(RE + 'src/' + f)
open(RE + 'src/_preamble.c', 'w', encoding='utf-8').write(''.join(pre))
for grp, fns in sorted(out.items()):
    open(RE + 'src/%s.c' % grp, 'w', encoding='utf-8').write('// Group: %s (%d functions)\n\n' % (grp, len(fns)) + '\n'.join(fns))
    print('%-14s %5d' % (grp, len(fns)))
