"""Extract the order objects a nation creates (FUN_004b2570): class, slot stored at nation+off, and Init(nation,a,b,c,d) args."""
import re, sys

RE = 'C:/GOG Games/Imperialism-RE/'
src = open(RE + 'imperialism_named.c', encoding='utf-8', errors='replace').read()
i = src.index('// FUN_004b2570 @')
body = src[i:src.index('\n// ', i + 20)]
cls = None
for ln in body.splitlines():
    m = re.search(r'\*piVar5 = \(int\)&(\w+)_vtable|= &(\w+)_vtable', ln)
    if m:
        cls = m[1] or m[2]
    m = re.search(r'\(\*\*\(code \*\*\)\(\*(?:piVar5|puVar\d+|iVar\d+) \+ (0x\w+)\)\)\((.*)\)', ln)
    if m and 'param_1' in m[2]:
        init = (m[1], m[2])
    m = re.search(r'\*\(int \*\*\)\(param_1 \+ (0x\w+)\) = \w+;', ln)
    if m and cls:
        print(cls, 'stored at', m[1], 'init', init)
