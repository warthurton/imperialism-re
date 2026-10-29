import sys; sys.path.insert(0, "C:/GOG Games/Imperialism-RE/tools")
import struct
from gob_res import load, walk
b, secs, r = load('C:/GOG Games/Imperialism/Data/STR#ENU.GOB')
out = {}
for t, blk, lang, off, size in walk(b, secs, r):
    p = off; end = off + size
    for i in range(16):
        if p + 2 > end: break
        l = struct.unpack_from('<H', b, p)[0]; p += 2
        if l:
            out[(blk - 1) * 16 + i] = b[p:p + 2 * l].decode('utf-16le', 'replace')
        p += 2 * l
with open('game_strings.txt', 'w', encoding='utf-8') as f:
    for k in sorted(out): f.write(f'{k}\t{out[k]!r}\n')
print(len(out), 'strings')
