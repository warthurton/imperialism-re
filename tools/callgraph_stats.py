"""Read-only: how much of the decompile is game logic, and how much of it is reachable from the turn simulation.

Run from the repo root after tools/split_source.py has written src/*.c (git-ignored). Prints, per group, the function count and how many still
carry a Ghidra name (FUN_xxxxxxxx), then follows DIRECT calls from the start points (default TSimMgr_AdvancePhase 0x57da70, the per-phase turn driver) and
prints the reachable functions per group and how many of those are named. Calls made through vtables (`(**(code **)(*p + 0x38))()`) are not followed, so the
reachable set is a lower bound; the numbers are for planning, not proof.

Usage: python -I tools/callgraph_stats.py [hexaddr ...]      (extra start addresses are added to the default)
       python -I tools/callgraph_stats.py --list-unnamed GROUP   (print the still-unnamed reachable functions of one group, biggest first)"""
import collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'src')
LIB = ('crt', 'mfc', 'link_stubs', 'static_init', 'dtor_wrappers', 'framework')
HEAD = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
CALL = re.compile(r'\b(?:thunk_)?(FUN_([0-9a-f]{8})|[A-Za-z_][A-Za-z0-9_]*)\s*\(')


def load():
    funcs = {}                    # addr -> (name, group, size in lines, body)
    for f in glob.glob(os.path.join(SRC, '*.c')):
        group = os.path.basename(f)[:-2]
        if group.startswith('_'):
            continue
        text = open(f, encoding='utf-8', errors='replace').read()
        parts = HEAD.split(text)
        for i in range(1, len(parts) - 2, 3):
            name, addr, body = parts[i], parts[i + 1], parts[i + 2]
            funcs[addr] = (name, group, body.count('\n'), body)
    return funcs


def main():
    args = sys.argv[1:]
    funcs = load()
    by_name = {v[0]: a for a, v in funcs.items()}
    thunks = {}                   # thunk address -> real address, from link_stubs bodies that just call one function
    for a, (n, g, sz, body) in funcs.items():
        if n.startswith('thunk_') and sz < 12:
            m = re.search(r'\b(?:thunk_)?FUN_([0-9a-f]{8})\s*\(', body)
            if m:
                thunks[a] = m.group(1)

    def callees(addr):
        out = set()
        for m in CALL.finditer(funcs[addr][3]):
            if m.group(2):
                t = m.group(2)
            else:
                t = by_name.get(m.group(1)) or by_name.get('thunk_' + m.group(1))
            if t and t in funcs and t != addr:
                out.add(thunks.get(t, t))
        return out

    if args and args[0] == '--list-unnamed':
        group = args[1]
        starts = ['0057da70']
    else:
        group = None
        starts = ['0057da70'] + [a.lower().zfill(8) for a in args]
    seen, todo = set(), [s for s in starts if s in funcs]
    while todo:
        a = todo.pop()
        if a in seen:
            continue
        seen.add(a)
        todo += [c for c in callees(a) if c not in seen]

    def named(a):
        return not re.match(r'(thunk_)?FUN_[0-9a-f]{8}$', funcs[a][0])

    if group:
        rows = sorted(((funcs[a][2], a) for a in seen if funcs[a][1] == group and not named(a)), reverse=True)
        for sz, a in rows:
            print('%s  %5d lines  %s' % (a, sz, funcs[a][0]))
        print(len(rows), 'unnamed reachable functions in', group)
        return
    tot, nam, lines = collections.Counter(), collections.Counter(), collections.Counter()
    for a, (n, g, sz, _) in funcs.items():
        tot[g] += 1
        nam[g] += named(a)
        lines[g] += sz
    reach, reach_n, reach_l = collections.Counter(), collections.Counter(), collections.Counter()
    for a in seen:
        g = funcs[a][1]
        reach[g] += 1
        reach_n[g] += named(a)
        reach_l[g] += funcs[a][2]
    print('%-14s %7s %7s %9s | %9s %7s %9s' % ('group', 'funcs', 'named', 'lines', 'reachable', 'named', 'lines'))
    for g in sorted(tot, key=lambda k: -tot[k]):
        print('%-14s %7d %7d %9d | %9d %7d %9d%s' % (g, tot[g], nam[g], lines[g], reach[g], reach_n[g], reach_l[g], '   (library)' if g in LIB else ''))
    game = [g for g in tot if g not in LIB]
    print('%-14s %7d %7d %9d | %9d %7d %9d' % ('GAME TOTAL', sum(tot[g] for g in game), sum(nam[g] for g in game), sum(lines[g] for g in game),
                                             sum(reach[g] for g in game), sum(reach_n[g] for g in game), sum(reach_l[g] for g in game)))
    print('start points: %s; direct calls only (vtable calls not followed)' % ', '.join(starts))


if __name__ == '__main__':
    main()
