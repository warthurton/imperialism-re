# Usage: python -I tools/diff_snapshot.py before.json after.json [--raw] [--limit 50]
import argparse
import json
from pathlib import Path


def compare(before, after, include_raw=False):
    for snapshot in (before, after):
        if snapshot.get('status') != 'ok' or snapshot['result']['schema'] != 1:
            raise ValueError('expected a successful schema-1 snapshot')
    before, after = before['result'], after['result']
    changes = []
    for name in sorted(before['fields'].keys() | after['fields'].keys()):
        old, new = before['fields'].get(name), after['fields'].get(name)
        if old != new:
            changes.append({'field': name, 'before': old, 'after': new})
    block_changes = []
    for name in sorted(before['blocks'].keys() | after['blocks'].keys()):
        old, new = before['blocks'].get(name), after['blocks'].get(name)
        if old is None or new is None:
            block_changes.append({'block': name, 'change': 'added' if old is None else 'removed'})
            continue
        left, right = bytes.fromhex(old['hex']), bytes.fromhex(new['hex'])
        offsets = [offset for offset in range(max(len(left), len(right)))
                   if left[offset:offset + 1] != right[offset:offset + 1]]
        if offsets:
            change = {'block': name, 'changed_bytes': len(offsets)}
            if include_raw:
                change['bytes'] = [{'offset': offset,
                                    'before': left[offset] if offset < len(left) else None,
                                    'after': right[offset] if offset < len(right) else None}
                                   for offset in offsets]
            block_changes.append(change)
    return {'result': {'fields': changes, 'blocks': block_changes,
                       'equal': not changes and not block_changes},
            'status': 'ok', 'errors': [], 'warnings': [
                'Raw blocks include pointers and padding; relocation is not normalized. '
                'Equal means equal captured bytes, not complete game-state equivalence.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('--limit', type=int, default=50)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('limit must be nonnegative')
    report = compare(json.loads(args.before.read_text(encoding='utf-8')),
                     json.loads(args.after.read_text(encoding='utf-8')), args.raw)
    result = report['result']
    result['field_change_count'] = len(result['fields'])
    result['block_change_count'] = len(result['blocks'])
    result['fields'] = result['fields'][:args.limit]
    for block in result['blocks']:
        if 'bytes' in block:
            block['bytes'] = block['bytes'][:args.limit]
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if result['equal'] else 1)


if __name__ == '__main__':
    main()
