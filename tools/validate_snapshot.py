# Usage: python -I tools/validate_snapshot.py results/snapshot_live
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diff_snapshot import compare


def validate(prefix):
    snapshots = {label: json.loads(Path(str(prefix) + '_' + label + '.json').read_text())
                 for label in ('before', 'idle', 'after')}
    checks = []
    for label in ('before', 'after'):
        state = snapshots[label]['result']
        reader_label = prefix.name + '_' + label
        city = json.loads((prefix.parent / ('city_' + reader_label + '.json')).read_text())
        power = state['fields']['game.local_power']
        if city['nation_index'] != power:
            raise ValueError('local power differs from independent city reader')
        city_block = state['blocks']['city.%d' % power]
        if city_block['hex'] != city['city_raw'][:city_block['size'] * 2]:
            raise ValueError(label + ': city differs from independent reader')
        for block, stem in [('technology', 'tech'), ('diplomacy', 'diplo')]:
            reader_raw = (prefix.parent / (stem + '_' + reader_label + '.bin')).read_bytes()
            if bytes.fromhex(state['blocks'][block]['hex']) != reader_raw:
                raise ValueError(label + ': ' + block + ' differs from independent reader')
        checks.extend([label + '.city', label + '.technology', label + '.diplomacy'])
    idle = compare(snapshots['before'], snapshots['idle'])['result']
    if not idle['equal']:
        raise ValueError('idle state changed: ' + json.dumps(idle))
    checks.append('idle_identity')
    before, after = snapshots['before']['result'], snapshots['after']['result']
    if after['fields']['game.turn'] != before['fields']['game.turn'] + 1:
        raise ValueError('expected exactly one completed turn')
    checks.append('one_turn')
    changes = compare(snapshots['before'], snapshots['after'])['result']
    return {'status': 'ok', 'checks': checks, 'field_changes': len(changes['fields']),
            'block_changes': len(changes['blocks']),
            'blocks_before': len(before['blocks']), 'blocks_after': len(after['blocks']),
            'decoded_fields': len(before['fields']),
            'turn_before': before['fields']['game.turn'], 'turn_after': after['fields']['game.turn'],
            'economic_changes': [change for change in changes['fields']
                                 if '.stock.' in change['field'] or change['field'].endswith('.cash')]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args()
    report = validate(args.prefix)
    output = Path(str(args.prefix) + '_validation.json')
    with output.open('x', encoding='utf-8') as destination:
        json.dump(report, destination, indent=2)
    print(json.dumps(report, indent=2))
