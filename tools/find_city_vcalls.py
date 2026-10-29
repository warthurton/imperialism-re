"""Find virtual calls on a TCity: locals loaded from nation+0x894 that are then used as the receiver of a vtable call.
Usage: find_city_vcalls.py 0x30 [0x28 ...]   (vtable byte offsets; 0x28 = BeginTurn, 0x30 = CompleteOrders)"""
import re, sys

RE = 'C:/GOG Games/Imperialism-RE/'
offs = [o.lower() for o in sys.argv[1:]]
cur = None; buf = []


def flush():
    if not cur:
        return
    text = ''.join(buf)
    # variables assigned from "... + 0x894)" (pointer or int typed)
    vars_ = set(re.findall(r'(\w+) = \*\(int \*+\)\([^;]*\+ 0x894\)', text))
    vars_ |= set(re.findall(r'(\w+) = \(int \*\)\*\(int \*\)\([^;]*\+ 0x894\)', text))
    for v in vars_:
        for o in offs:
            for pat in (r'\*\*?%s \+ %s\)\)' % (v, o), r'\(\*%s \+ %s\)' % (v, o), r'\*\(int \*\)%s \+ %s\)' % (v, o)):
                if re.search(pat, text):
                    print('%-48s var=%-8s slot %s' % (cur, v, o))
                    return
    # direct form: **(int **)(X + 0x894) + off
    for o in offs:
        if re.search(r'\*\*\(int \*\*\)\([^;]*\+ 0x894\) \+ %s\)' % o, text):
            print('%-48s direct slot %s' % (cur, o))


for ln in open(RE + 'imperialism_named.c', encoding='utf-8', errors='replace'):
    m = re.match(r'// (\S+) @ ([0-9a-f]{8})', ln)
    if m:
        flush()
        cur = m[1] + '@' + m[2]; buf = []
    else:
        buf.append(ln)
flush()
