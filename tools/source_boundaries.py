"""Read-only: narrow the 'boundary' zones of names/source_attribution.tsv (written by tools/source_files.py).

A boundary zone is a run of functions between two anchored source files A (earlier) and B (later). The linker lays each file's functions out contiguously, so inside a zone the
files switch exactly once: functions 0..k-1 belong to A, k.. to B (or to a third file with no assert at all, when the zone is long). Evidence per function:
  * class: a function named TClass_something belongs to the file most of that class's already-attributed methods are in;
  * calls: direct calls to / from already-attributed functions vote for their files (library code ignored).
For each zone we pick the cut k with the best score and mark a function resolved only if every cut with the best score agrees on its side; the rest stay 'boundary'.
The pass repeats, since each resolved function adds evidence. Rewrites names/source_attribution.tsv ('how' becomes 'cut' for resolved functions).

Needs src/*.c. Usage: python -I tools/source_files.py && python -I tools/source_boundaries.py"""
import collections, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
LIB = ('crt', 'mfc', 'link_stubs', 'static_init', 'dtor_wrappers')
CLASS = re.compile(r'^T[A-Za-z0-9]+(?=_)')
CALL = re.compile(r'\b(?:thunk_)?FUN_([0-9a-f]{8})\s*\(')
EH = re.compile(r'puStack_8\s*=\s*&?(?:\(undefined \*\))?(?:UNK|LAB|DAT|PTR_LAB|FUN)_([0-9a-f]{8})')
NAMEDCALL = re.compile(r'\b(T[A-Za-z0-9]+_[A-Za-z0-9_]+)\s*\(')


UI_SUFFIX = re.compile(r'^T[A-Za-z0-9]*(View|Dialog|Picture|Cluster|Window|Line|Floater|Toolbar|Button|Slider|Control|Placard|Pane|Icon|Box|Text|Page|Dlog)(_|$)')
UI_FILE = re.compile(r'(Views|Dialogs|Dlog|Screens|Icon|DisplayMgr|ViewMgr|SuperMap|HelpMgr|GameWindow|McApp|QuickDraw|CDib|IncludeView)')


def ui_class(name):
    """True for a view/dialog/control class name, False for a TClass_ name that is not one, None for unnamed functions (no evidence)."""
    m = CLASS.match(name)
    if not m:
        return None
    return bool(UI_SUFFIX.match(name))


def ui_file(fn):
    return bool(UI_FILE.search(fn))


def main():
    import sys
    debug = sys.argv[1] if len(sys.argv) > 1 else None           # e.g. "Cross/UCity.cpp|Cross/UCityDialogs.cpp": print the evidence of that zone (first round)
    funcs = {}
    for f in glob.glob(os.path.join(ROOT, 'src', '*.c')):
        g = os.path.basename(f)[:-2]
        if g.startswith('_'):
            continue
        parts = HEAD.split(open(f, encoding='utf-8', errors='replace').read())
        for i in range(1, len(parts) - 2, 3):
            funcs[int(parts[i + 1], 16)] = (parts[i], g, parts[i + 2])
    path = os.path.join(ROOT, 'names', 'source_attribution.tsv')
    rows = []
    for line in open(path, encoding='utf-8'):
        a, n, fn, how, ln = line.rstrip('\n').split('\t')
        rows.append([int(a, 16), n, fn, how, ln])
    by_name = {v[0]: a for a, v in funcs.items()}
    thunk = {}
    for a, (n, g, b) in funcs.items():
        if n.startswith('thunk_') and b.count('\n') < 12:
            m = CALL.search(b)
            if m:
                thunk[a] = int(m.group(1), 16)
    callees = collections.defaultdict(set)
    callers = collections.defaultdict(set)
    for a, (n, g, b) in funcs.items():
        if g in LIB:
            continue
        for m in CALL.finditer(b):
            t = int(m.group(1), 16)
            t = thunk.get(t, t)
            if t in funcs and t != a and funcs[t][1] not in LIB:
                callees[a].add(t)
                callers[t].add(a)
        for m in NAMEDCALL.finditer(b):
            t = by_name.get(m.group(1))
            if t and t != a and funcs[t][1] not in LIB:
                callees[a].add(t)
                callers[t].add(a)
    # Exception-handler stubs: a function with unwinding code stores the address of its stub in its frame (puStack_8 = &UNK_0062a8f6). The stubs sit in one
    # region in link order, so the stub addresses of one file's functions form an interval, and the intervals follow the file order (checked: no file out of order).
    eh = {}
    for a, (n, g, b) in funcs.items():
        m = EH.search(b)
        if m and g not in LIB:
            eh[a] = int(m.group(1), 16)
    start_unres = sum(1 for r in rows if r[3] == 'boundary')
    for rnd in range(8):
        use_prior = rnd >= 3                  # rounds 0-2: hard evidence only (class, stub order); later rounds add the semantic prior and label its results 'prior'
        certain = {r[0]: r[2] for r in rows if r[3] != 'boundary'}
        span = {}
        for r in rows:
            if r[3] in ('assert', 'inferred') and r[0] in eh:
                lo, hi = span.get(r[2], (eh[r[0]], eh[r[0]]))
                span[r[2]] = (min(lo, eh[r[0]]), max(hi, eh[r[0]]))
        cls = collections.defaultdict(collections.Counter)
        for a, fn in certain.items():
            m = CLASS.match(funcs[a][0])
            if m:
                cls[m.group(0)][fn] += 1

        def votes(a, A, B):
            va = vb = 0
            m = CLASS.match(funcs[a][0])
            if m and m.group(0) in cls:
                c = cls[m.group(0)]
                tot = sum(c.values())
                if tot >= 2 and max(c.values()) >= 0.9 * tot:      # a class whose already-attributed methods are (nearly) all in one file
                    va += 3 * c[A] / tot
                    vb += 3 * c[B] / tot
            # Call-graph votes were tried and removed: UI code calls into game logic, so the callers of a logic function vote for the UI file and pull the cut
            # to the wrong place (seen in the UCity.cpp | UCityDialogs.cpp zone).
            if use_prior and not (va or vb):
                ui = ui_class(funcs[a][0])
                if ui is not None and ui_file(A) != ui_file(B):
                    # a view/dialog class is expected in the Views/Dialogs file, anything else in the logic file; weight 1, below the hard evidence
                    if ui == ui_file(A):
                        va += 1
                    else:
                        vb += 1
            v = eh.get(a)
            if v is not None:
                if A in span and v <= span[A][1] and (v >= span[A][0] or B not in span or v < span[B][0]):
                    va += 5                                    # inside or before A's stub interval, and not into B's
                if B in span and v >= span[B][0] and (v <= span[B][1] or A not in span or v > span[A][1]):
                    vb += 5
            return va, vb
        changed = 0
        i = 0
        while i < len(rows):
            if rows[i][3] != 'boundary':
                i += 1
                continue
            j = i
            while j < len(rows) and rows[j][3] == 'boundary' and rows[j][2] == rows[i][2]:
                j += 1
            A, B = rows[i][2].split('|')
            zone = rows[i:j]
            ev = [votes(r[0], A, B) for r in zone]
            n = len(zone)
            pre = [0.0]
            for va, vb in ev:
                pre.append(pre[-1] + va)
            suf = [0.0] * (n + 1)
            for k in range(n - 1, -1, -1):
                suf[k] = suf[k + 1] + ev[k][1]
            score = [pre[k] + suf[k] for k in range(n + 1)]
            best = max(score)
            ks = [k for k in range(n + 1) if score[k] >= best - 1e-9]
            if debug and rnd == 0 and rows[i][2] == debug:
                print('zone %s: %d functions, best score %.1f, cuts %d..%d' % (debug, n, best, min(ks), max(ks)))
                for idx, (r, (va, vb)) in enumerate(zip(zone, ev)):
                    print('  %3d %08x %-34s A %.1f B %.1f  eh %s' % (idx, r[0], funcs[r[0]][0][:34], va, vb, '%08x' % eh[r[0]] if r[0] in eh else '-'))
                print('  spans: A %s  B %s' % (tuple('%08x' % x for x in span[A]) if A in span else None, tuple('%08x' % x for x in span[B]) if B in span else None))
            if best > 0:
                # Conservative: only the part of the zone that lies on the evidence side of every best cut is resolved. A functions stop at the last A evidence
                # before the cut, B functions start at the first B evidence after it; the stretch in between has no evidence and stays open.
                lo, hi = min(ks), max(ks)
                a_last = max((x for x in range(lo) if ev[x][0] > ev[x][1]), default=-1)
                b_first = min((x for x in range(hi, n) if ev[x][1] > ev[x][0]), default=n)
                for idx in range(n):
                    if idx <= a_last:
                        zone[idx][2], zone[idx][3] = A, 'prior' if use_prior else 'cut'
                        changed += 1
                    elif idx >= b_first:
                        zone[idx][2], zone[idx][3] = B, 'prior' if use_prior else 'cut'
                        changed += 1
            i = j
        if not changed and use_prior:
            break
    left = sum(1 for r in rows if r[3] == 'boundary')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for a, n, fn, how, ln in rows:
            f.write('%08x\t%s\t%s\t%s\t%s\n' % (a, n, fn, how, ln))
    how = collections.Counter(r[3] for r in rows)
    print('boundary functions: %d before, %d after: %d resolved by hard evidence (class, stub order), %d by the semantic prior (view/dialog vs logic), %d still open' % (
        start_unres, left, how['cut'], how['prior'], left))
    zones = collections.Counter(r[2] for r in rows if r[3] == 'boundary')
    for z, c in zones.most_common(12):
        print('  still open: %-50s %d functions' % (z, c))


if __name__ == '__main__':
    main()
