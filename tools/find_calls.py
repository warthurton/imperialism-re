"""List functions in imperialism_named.c whose body matches all given regexes (usage: find_calls.py rx1 rx2 ...)."""
import re, sys

RE = 'C:/GOG Games/Imperialism-RE/'
pats = [re.compile(p) for p in sys.argv[1:]]
cur = None; buf = []


def flush():
    if cur and all(p.search(''.join(buf)) for p in pats):
        print(cur, len(buf))


for ln in open(RE + 'imperialism_named.c', encoding='utf-8', errors='replace'):
    m = re.match(r'// (\S+) @ ([0-9a-f]{8})', ln)
    if m:
        flush()
        cur = m[1] + '@' + m[2]; buf = []
    else:
        buf.append(ln)
flush()
