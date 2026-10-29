"""Turn lib_matches.tsv (from match_lib.py) into lib_names.json: {exe address -> readable identifier}.

Only unambiguous matches are used: a single candidate name, at least MIN_SIZE bytes, and not an anonymous
section. MSVC-decorated names are converted to Class__Method style identifiers (overloads get an address suffix).
"""
import csv, json, re

RE = 'C:/GOG Games/Imperialism-RE/'
MIN_SIZE = 16
OPS = {'0': 'ctor', '1': 'dtor', '4': 'op_assign', '8': 'op_eq', '9': 'op_ne', 'A': 'op_index', 'C': 'op_arrow',
       'D': 'op_deref', 'H': 'op_plus', 'G': 'op_minus', '_G': 'scalar_deleting_dtor', '_E': 'vector_deleting_dtor',
       '_7': 'vftable', '_0': 'op_div', '2': 'op_new', '3': 'op_delete', 'Y': 'op_pluseq', 'Z': 'op_minuseq',
       'M': 'op_lt', 'N': 'op_le', 'O': 'op_gt', 'P': 'op_ge', 'B': 'op_cast'}


def readable(mangled):
    n = mangled
    if n.startswith('?$') or not n.startswith('?'):          # C names: _memcmp, ___sbh_alloc_block, @fastcall@..
        n = n.split('@')[0] if n.startswith('@') is False else n
        return 'crt' + re.sub(r'[^A-Za-z0-9_]', '_', n if n.startswith('_') else '_' + n)
    body = n[1:]
    if body.startswith('?_'):
        code = body[1:3]; rest = body[3:]
        cls = rest.split('@')[0]
        return re.sub(r'\W', '_', cls) + '__' + OPS.get(code, 'special' + code.strip('_'))
    if body.startswith('?'):
        code = body[1]; rest = body[2:]
        cls = rest.split('@')[0]
        return re.sub(r'\W', '_', cls) + '__' + OPS.get(code, 'op' + code)
    parts = body.split('@')
    meth = parts[0]; cls = parts[1] if len(parts) > 2 and parts[1] else ''
    return re.sub(r'\W', '_', cls + '__' + meth) if cls else re.sub(r'\W', '_', meth)


rows = list(csv.DictReader(open(RE + 'lib_matches.tsv'), delimiter='\t'))
names = {}
skipped = 0
for r in rows:
    if r['distinct_names'] != '1' or int(r['size']) < MIN_SIZE or '#' in r['name']:
        skipped += 1
        continue
    names[r['va']] = (readable(r['name']), r['name'])
seen = {}
for va, (rd, raw) in names.items():
    seen.setdefault(rd, []).append(va)
out = {}
for va, (rd, raw) in names.items():
    out[va] = rd if len(seen[rd]) == 1 else '%s_%s' % (rd, va[2:])
json.dump({'funcs': out, 'raw': {va: raw for va, (rd, raw) in names.items()}}, open(RE + 'lib_names.json', 'w'), indent=0)
print(len(out), 'library functions named;', skipped, 'matches skipped (ambiguous/short/anonymous)')
