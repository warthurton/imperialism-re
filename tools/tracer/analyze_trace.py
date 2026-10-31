"""Summarise a trace written by tools/tracer/trace_calls.exe: which functions ran, in which turn phase, in which group and source file.

Usage: python -I tools/tracer/analyze_trace.py results/trace3 [--phase N] [--unnamed GROUP]
  default        counts per phase, per group and per original source file; the functions never reached from any phase tag are counted as 'untagged'
  --phase N      list the functions first seen in phase N in call order, with names and callers
  --unnamed G    list hit functions of group G that still have only an auto name (candidates to decode next), most called first
The phase is the value the trace tagged each hit with (the turn driver's current phase, 31 = before the first phase was seen)."""
import collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)


def main():
    args = sys.argv[1:]
    prefix = args[0]
    funcs = {}
    for f in glob.glob(os.path.join(ROOT, 'src', '*.c')):
        g = os.path.basename(f)[:-2]
        if g.startswith('_'):
            continue
        for m in HEAD.finditer(open(f, encoding='utf-8', errors='replace').read()):
            funcs[int(m.group(2), 16)] = (m.group(1), g)
    attr = {}
    p = os.path.join(ROOT, 'names', 'source_attribution.tsv')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            a, n, fn, how, ln = line.rstrip('\n').split('\t')
            attr[int(a, 16)] = (fn, how)
    hits = {}
    for line in open(prefix + '_funcs.tsv', encoding='utf-8'):
        a, h, seq, ph, caller, capped = line.split()
        hits[int(a, 16)] = (int(h), int(seq), int(ph, 16), int(caller, 16), int(capped))
    if '--export' in args:
        out = args[args.index('--export') + 1]
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# addr\tname\tgroup\tsource file (names/source_attribution.tsv)\thits (capped)\tfirst_seq\tphase mask (bit n = phase n)\tfirst caller\n')
            for a, (h, seq, ph, caller, capped) in sorted(hits.items(), key=lambda kv: kv[1][1]):
                n, g = funcs.get(a, ('?', '?'))
                fh.write('%08x\t%s\t%s\t%s\t%d\t%d\t%08x\t%s\n' % (a, n, g, attr.get(a, ('', ''))[0], h, seq, ph, funcs.get(caller, ('-', ''))[0] if caller else '-'))
        print('%d functions written to %s' % (len(hits), out))
        return
    if '--phase' in args:
        ph = int(args[args.index('--phase') + 1])
        rows = sorted((v[1], a) for a, v in hits.items() if v[2] >> ph & 1)
        for seq, a in rows:
            n, g = funcs.get(a, ('?', '?'))
            c = hits[a][3]
            print('%5d %08x %-40s %-12s from %s' % (seq, a, n[:40], g, funcs.get(c, ('-', ''))[0][:32] if c else '-'))
        return
    if '--unnamed' in args:
        grp = args[args.index('--unnamed') + 1]
        rows = sorted(((v[0], a) for a, v in hits.items() if funcs.get(a, ('', ''))[1] == grp and re.match(r'FUN_', funcs[a][0])), reverse=True)
        for h, a in rows:
            print('%08x %8d hits  %s' % (a, h, attr.get(a, ('?', ''))[0]))
        print(len(rows), 'unnamed functions hit in', grp)
        return
    phases = collections.Counter()
    for a, (h, seq, ph, caller, capped) in hits.items():
        for b in range(32):
            if ph >> b & 1:
                phases[b] += 1
    print('functions hit: %d' % len(hits))
    print('per phase (a function can be in several): ' + ', '.join('%d:%d' % (b, phases[b]) for b in sorted(phases)))
    byg = collections.Counter(funcs.get(a, ('?', '?'))[1] for a in hits)
    named = collections.Counter(funcs.get(a, ('?', '?'))[1] for a in hits if not re.match(r'(thunk_)?FUN_', funcs.get(a, ('FUN_', ''))[0]))
    print('\nper group (hit / of which with a structural or meaning name):')
    for g, c in byg.most_common():
        print('  %-14s %5d  %5d' % (g, c, named[g]))
    byf = collections.Counter(attr.get(a, ('(unattributed)', ''))[0] for a in hits)
    print('\nper original source file:')
    for g, c in byf.most_common(30):
        print('  %-30s %5d' % (g, c))


if __name__ == '__main__':
    main()
