"""Read-only: attribute functions to the original source files using the assert/file-name strings left in the exe.

The game calls one assert function, FUN_0049d620(file_string, line), from about 360 places; the file string is the compile-time __FILE__ ("D:\\Ambit\\Cross\\UCity.cpp").
Every call site therefore names the .cpp file its function came from, and the line number. The linker lays a translation unit's functions out contiguously, so the
functions between two anchors of the same file belong to it too (marked 'inferred'); functions between anchors of two different files are 'boundary' (either file).

Needs src/*.c (tools/split_source.py) and results/exe_strings_flagged.tsv (tools/exe_strings.py). Usage:
  python -I tools/source_files.py            writes names/source_attribution.tsv (addr, name, file, how, lines) and prints a summary per file
Columns of the tsv: addr, current name, source file, 'assert' | 'inferred' | 'boundary', assert line numbers seen in that function."""
import collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
CALL = re.compile(r'(?:FUN_0049d620|Ambit_Assert)\(\s*(s_[A-Za-z0-9_]+_([0-9a-f]{8}))\s*(?:,\s*(0x[0-9a-f]+|\d+))?')    # the hook is named Ambit_Assert since names.tsv row 0049d620


def file_strings():
    out = {}
    for line in open(os.path.join(ROOT, 'results', 'exe_strings_flagged.tsv'), encoding='utf-8'):
        va, sec, flags, text = line.rstrip('\n').split('\t', 3)
        if 'file' in flags and ('Ambit' in text):
            out[int(va, 16)] = text
    return out


def main():
    strings = file_strings()
    funcs = {}
    for f in glob.glob(os.path.join(ROOT, 'src', '*.c')):
        group = os.path.basename(f)[:-2]
        if group.startswith('_'):
            continue
        parts = HEAD.split(open(f, encoding='utf-8', errors='replace').read())
        for i in range(1, len(parts) - 2, 3):
            funcs[int(parts[i + 1], 16)] = (parts[i], group, parts[i + 2])
    anchors = {}                                  # addr -> (file, [lines])
    for a, (name, group, body) in funcs.items():
        for m in CALL.finditer(body):
            path = strings.get(int(m.group(2), 16))
            if not path:
                continue
            fn = path.replace('\\', '/').split('/Ambit/', 1)[-1] if '/Ambit/' in path.replace('\\', '/') else path
            fn = re.sub(r'^.*Ambit/', '', path.replace('\\', '/'), flags=re.I)
            e = anchors.setdefault(a, [fn, [], int(m.group(2), 16)])
            if m.group(3):
                e[1].append(int(m.group(3), 0))
    # Header files (.h) and shared inline code put file strings into functions that live elsewhere. Both the string pool and the code follow link order,
    # so keep only the .cpp anchors that fit one increasing order (longest non-decreasing run of string address against function address).
    cand = sorted(a for a in anchors if anchors[a][0].lower().endswith('.cpp'))
    best = [(anchors[a][2], i) for i, a in enumerate(cand)]
    import bisect
    tails, tails_idx, prev = [], [], [-1] * len(cand)
    for i, (sva, _) in enumerate(best):
        pos = bisect.bisect_right(tails, sva)
        if pos == len(tails):
            tails.append(sva); tails_idx.append(i)
        else:
            tails[pos] = sva; tails_idx[pos] = i
        prev[i] = tails_idx[pos - 1] if pos else -1
    keep, k = set(), tails_idx[-1] if tails_idx else -1
    while k != -1:
        keep.add(cand[k]); k = prev[k]
    ignored = [(a, anchors[a][0]) for a in anchors if a not in keep]
    anchors = {a: v for a, v in anchors.items() if a in keep}
    order = sorted(a for a, (n, g, b) in funcs.items() if g not in ('crt', 'mfc', 'link_stubs', 'static_init', 'dtor_wrappers'))
    rows, last = [], None
    anchored = [a for a in order if a in anchors]
    for idx, a in enumerate(order):
        if a in anchors:
            rows.append((a, anchors[a][0], 'assert', anchors[a][1]))
            continue
        prev = max((x for x in anchored if x < a), default=None)
        nxt = min((x for x in anchored if x > a), default=None)
        if prev is None or nxt is None:
            continue
        if anchors[prev][0] == anchors[nxt][0]:
            rows.append((a, anchors[prev][0], 'inferred', []))
        else:
            rows.append((a, anchors[prev][0] + '|' + anchors[nxt][0], 'boundary', []))
    with open(os.path.join(ROOT, 'names', 'source_attribution.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        for a, fn, how, lines in rows:
            f.write('%08x\t%s\t%s\t%s\t%s\n' % (a, funcs[a][0], fn, how, ','.join(str(x) for x in sorted(set(lines)))))
    per = collections.defaultdict(lambda: collections.Counter())
    span = {}
    for a, fn, how, lines in rows:
        per[fn][how] += 1
        lo, hi = span.get(fn, (a, a))
        span[fn] = (min(lo, a), max(hi, a))
    print('%d usable anchors (%d ignored: header or shared inline code), %d source files; %d of %d non-library functions attributed' % (len(anchors), len(ignored), len([f for f in per if '|' not in f]), len(rows), len(order)))
    for fn in sorted(per, key=lambda k: span[k][0]):
        c = per[fn]
        print('%-34s %08x-%08x  assert %3d  inferred %4d  boundary %3d' % (fn, span[fn][0], span[fn][1], c['assert'], c['inferred'], c['boundary']))


if __name__ == '__main__':
    main()
