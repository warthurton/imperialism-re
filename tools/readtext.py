"""Read the text the game draws, from the shim's text log (needs the text-logging shim and `[text_log] enabled=1` in the game's
imperialism_shim.ini; harness/prod_boot.ps1 switches it on). The game draws each string twice (a shadow one pixel up-left), and redraws
screens, so lines are collapsed.
Usage: python -I readtext.py mark                 prints the current end of the log (a byte offset)
       python -I readtext.py since <offset>       text drawn since that offset, collapsed, one "x,y text" per line
       python -I readtext.py tail [N]             the last N (default 40) collapsed lines
Idea: `mark`, do something in the game, then `since <mark>` = what the game drew in response."""
import os, sys

LOG = 'C:/GOG Games/Imperialism/imperialism_text.log'


def lines_from(offset):
    with open(LOG, 'rb') as f:
        f.seek(offset)
        data = f.read().decode('latin-1')
    out = []
    for ln in data.split('\n'):
        p = ln.split(' ', 3)
        if len(p) < 4:
            continue
        tick, kind, xy, text = p
        try:
            x, y = (int(v) for v in xy.split(','))
        except ValueError:
            continue
        out.append((int(tick), kind, x, y, text))
    return out


def collapse(rows):
    """drop the shadow copy (same text, within 2 px, same tick) and exact repeats"""
    seen, res = set(), []
    for tick, kind, x, y, text in rows:
        if any((tick, text, x + dx, y + dy) in seen for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)):
            continue
        seen.add((tick, text, x, y))
        res.append((x, y, text))
    return res


if sys.argv[1] == 'mark':
    print(os.path.getsize(LOG))
elif sys.argv[1] == 'since':
    for x, y, t in collapse(lines_from(int(sys.argv[2]))):
        print('%d,%d %s' % (x, y, t))
elif sys.argv[1] == 'tail':
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    for x, y, t in collapse(lines_from(0))[-n:]:
        print('%d,%d %s' % (x, y, t))
