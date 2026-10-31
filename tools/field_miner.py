# Usage: python -I tools/field_miner.py [--object TCity] [--output results/fields.tsv]
import argparse
import collections
import csv
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER = re.compile(r'^// (\S+) @ ([0-9a-f]{8})', re.M)
TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
                   r'0x[0-9a-fA-F]+|\d+|[A-Za-z_]\w*|<<=|>>=|\+\+|--|->|'
                   r'\+=|-=|\*=|/=|%=|&=|\|=|\^=|==|!=|<=|>=|<<|>>|&&|\|\||[^\s]')
# Ch 18: keep Ghidra's primitive widths in one table; class sizes are not pointer strides.
WIDTHS = {'char': 1, 'byte': 1, 'bool': 1, 'undefined1': 1,
          'short': 2, 'ushort': 2, 'undefined2': 2,
          'int': 4, 'uint': 4, 'long': 4, 'ulong': 4, 'undefined4': 4, 'float': 4,
          'longlong': 8, 'ulonglong': 8, 'undefined8': 8, 'double': 8}
ASSIGNMENTS = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='}
GLOBAL_TYPES = {'g_Nations': ('int', 1), 'g_GreatPowers': ('int', 1),
                'g_Minors': ('int', 1)}


def type_info(tokens):
    words = [token for token in tokens if token not in ('const', 'volatile', 'signed', 'unsigned')]
    if not words or words[0] not in WIDTHS or any(token != '*' for token in words[1:]):
        return None
    depth = len(words) - 1
    return {'width': 4 if depth else WIDTHS[words[0]],
            'stride': (4 if depth > 1 else WIDTHS[words[0]]) if depth else 1,
            'pointer_depth': depth}


class AccessParser:
    def __init__(self, source, symbols, owner, address):
        self.tokens = [match[0] for match in TOKEN.finditer(source)
                       if not match[0].startswith(('//', '/*', '"', "'"))]
        self.symbols = symbols
        self.owner = owner
        self.address = address
        self.ends = {}
        stack = []
        for index, token in enumerate(self.tokens):
            if token in ('(', '['):
                stack.append((token, index))
            elif token in (')', ']') and stack:
                opening, start = stack.pop()
                if (opening, token) in (('(', ')'), ('[', ']')):
                    self.ends[start] = index

    def root(self, name):
        if name == 'param_1':
            label = self.owner or 'function.%08x.param_1' % self.address
            provenance = 'method_name' if self.owner else 'unattributed_parameter'
        elif name.startswith(('g_', 'DAT_')):
            label, provenance = name, 'global_symbol'
        else:
            return None
        symbol_type = self.symbols.get(name)
        return {'object': label, 'offset': 0,
                'stride': symbol_type['stride'] if symbol_type else None,
                'dynamic': False, 'provenance': provenance, 'path_resolved': True,
                'offset_resolved': True}

    def dereference(self, start, stop):
        # Match only a complete *(primitive *) expression, never a vtable code cast.
        tokens = self.tokens
        if start + 3 >= stop or tokens[start:start + 2] != ['*', '(']:
            return None
        type_end = self.ends.get(start + 1)
        if type_end is None or type_end + 1 >= stop:
            return None
        info = type_info(tokens[start + 2:type_end])
        if info is None or not info['pointer_depth']:
            return None
        operand_start = type_end + 1
        if tokens[operand_start] == '(':
            operand_end = self.ends.get(operand_start)
            if operand_end != stop - 1:
                return None
            operand_start += 1
        elif operand_start != stop - 1:
            return None
        else:
            operand_end = stop
        resolved = self.resolve(operand_start, operand_end)
        if resolved is None:
            return None
        width = 4 if info['pointer_depth'] > 1 else info['stride']
        return resolved, width, info['pointer_depth']

    def resolve(self, start, stop):
        tokens = self.tokens
        while start < stop and tokens[start] == '(' and self.ends.get(start) == stop - 1:
            start, stop = start + 1, stop - 1
        if start >= stop:
            return None
        # Split at top-level additions before casts: (int *)p + 2 scales differently from (int *)(p + 2).
        terms, position, term_start = [], start, start
        sign = 1
        while position < stop:
            if tokens[position] in ('(', '[') and position in self.ends:
                position = self.ends[position] + 1
                continue
            if tokens[position] in ('+', '-') and position > term_start:
                terms.append((sign, term_start, position))
                sign = 1 if tokens[position] == '+' else -1
                term_start = position + 1
            position += 1
        if terms:
            terms.append((sign, term_start, stop))
            base = None
            constant = 0
            dynamic = False
            for sign, term_start, term_end in terms:
                value_tokens = tokens[term_start:term_end]
                if len(value_tokens) == 2 and value_tokens[0] in ('+', '-'):
                    sign *= 1 if value_tokens[0] == '+' else -1
                    value_tokens = value_tokens[1:]
                if len(value_tokens) == 1 and re.fullmatch(r'0x[0-9a-fA-F]+|\d+', value_tokens[0]):
                    constant += sign * int(value_tokens[0], 0)
                    continue
                candidate = self.resolve(term_start, term_end)
                if candidate is not None:
                    if base is not None or sign != 1:
                        return None
                    base = candidate
                else:
                    dynamic = True
            if base is None:
                return None
            base = dict(base)
            if constant and base['stride'] is None:
                base['offset_resolved'] = False
            base['offset'] += constant * (base['stride'] or 1)
            base['dynamic'] |= dynamic
            return base
        if tokens[start] == '(' and start in self.ends:
            cast_end = self.ends[start]
            info = type_info(tokens[start + 1:cast_end])
            if info and cast_end < stop - 1:
                base = self.resolve(cast_end + 1, stop)
                if base:
                    base = dict(base)
                    base['stride'] = info['stride']
                return base
        nested = self.dereference(start, stop)
        if nested:
            base, width, depth = nested
            if width != 4 or base['dynamic']:
                return None
            base = dict(base)
            is_resolved = base['offset_resolved'] and base['path_resolved']
            suffix = '+0x%x' % base['offset'] if base['offset'] >= 0 else '-0x%x' % -base['offset']
            base['object'] += '->' + suffix + ('' if is_resolved else '?units')
            base.update(offset=0, stride=4 if depth > 1 else 1,
                        path_resolved=is_resolved, offset_resolved=True)
            return base
        if stop == start + 1:
            return self.root(tokens[start])
        return None

    def mode(self, start, stop):
        tokens = self.tokens
        # Parenthesized lvalues have the same access mode as an unwrapped dereference.
        while start and tokens[start - 1] == '(' and self.ends.get(start - 1) == stop:
            start, stop = start - 1, stop + 1
        following = tokens[stop] if stop < len(tokens) else ''
        preceding = tokens[start - 1] if start else ''
        if preceding == '&':
            before_ampersand = tokens[start - 2] if start > 1 else ''
            is_expression_end = bool(re.fullmatch(r'[A-Za-z_]\w*|0x[0-9a-fA-F]+|\d+', before_ampersand))
            is_expression_end |= before_ampersand in (')', ']')
            if not is_expression_end or before_ampersand == 'return':
                return 'address'
        if following == '=':
            return 'write'
        if following in ASSIGNMENTS or following in ('++', '--') or preceding in ('++', '--'):
            return 'read_write'
        return 'read'

    def accesses(self):
        accesses = []
        tokens = self.tokens
        for start, token in enumerate(tokens):
            if token == '*' and tokens[start + 1:start + 2] == ['(']:
                type_end = self.ends.get(start + 1)
                if type_end is None or type_end + 1 >= len(tokens):
                    continue
                operand_start = type_end + 1
                stop = self.ends.get(operand_start, operand_start) + 1
                access = self.dereference(start, stop)
                if access:
                    base, width, _ = access
                    accesses.append(self.record(base, width, self.mode(start, stop)))
            elif token == 'param_1' or token.startswith(('g_', 'DAT_')):
                if tokens[start + 1:start + 2] != ['[']:
                    continue
                end = self.ends.get(start + 1)
                symbol_type = self.symbols.get(token)
                if end is None or symbol_type is None or not symbol_type['pointer_depth']:
                    continue
                base = self.root(token)
                if end == start + 3 and re.fullmatch(r'0x[0-9a-fA-F]+|\d+', tokens[start + 2]):
                    base['offset'] = int(tokens[start + 2], 0) * symbol_type['stride']
                else:
                    base['dynamic'] = True
                accesses.append(self.record(base, symbol_type['stride'], self.mode(start, end + 1)))
        return accesses

    @staticmethod
    def record(base, width, mode):
        return {'object': base['object'], 'offset': base['offset'], 'width': width,
                'offset_kind': 'bytes' if base['offset_resolved'] else 'unknown_stride_units',
                'dynamic': base['dynamic'], 'path_resolved': base['path_resolved'],
                'mode': mode, 'provenance': base['provenance']}


def mine_function(name, address, body, classes):
    signature, separator, statements = body.partition('{')
    if not separator:
        return []
    symbols = {name: type_info([primitive] + ['*'] * depth)
               for name, (primitive, depth) in GLOBAL_TYPES.items()}
    # Only parameter declarations establish arithmetic scaling; aliases stay unresolved.
    for match in re.finditer(r'\b(unsigned\s+|signed\s+)?([A-Za-z_]\w*)\s*(\*+)?\s*(param_\d+)\b', signature):
        info = type_info([match[2]] + ['*'] * len(match[3] or ''))
        if info:
            symbols[match[4]] = info
    owner = None
    if '__thiscall' in signature or '__fastcall' in signature:
        owners = [class_name for class_name in classes if name.startswith(class_name + '_')]
        if owners:
            owner = max(owners, key=len)
    parser = AccessParser(statements, symbols, owner, address)
    return parser.accesses()


def mine(source, classes, object_filter=None):
    headers = list(HEADER.finditer(source))
    aggregate = {}
    analyzed = 0
    for index, header in enumerate(headers):
        name, address = header[1], int(header[2], 16)
        if address < 0x410000:
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
        analyzed += 1
        for access in mine_function(name, address, source[header.end():end], classes):
            if object_filter and access['object'] != object_filter and not access['object'].startswith(object_filter + '->'):
                continue
            key = tuple(access[field] for field in ('object', 'offset', 'width', 'offset_kind',
                                                    'dynamic', 'path_resolved', 'provenance'))
            row = aggregate.setdefault(key, dict(access, reads=0, writes=0, addresses=0, functions=set()))
            mode = access['mode']
            row['reads'] += mode in ('read', 'read_write')
            row['writes'] += mode in ('write', 'read_write')
            row['addresses'] += mode == 'address'
            row['functions'].add('%08x:%s' % (address, name))
    rows = []
    for _, row in sorted(aggregate.items()):
        row.pop('mode')
        row['functions'] = sorted(row['functions'])
        allocation = classes.get(row['object']) if isinstance(classes, dict) else None
        row['allocation_size'] = allocation
        row['within_allocation'] = None
        if allocation is not None and not row['dynamic'] and row['offset_kind'] == 'bytes':
            row['within_allocation'] = 0 <= row['offset'] and row['offset'] + row['width'] <= allocation
        rows.append(row)
    return {'result': {'functions_analyzed': analyzed, 'rows': rows}, 'status': 'ok', 'errors': [],
            'warnings': ['Candidates only: no alias analysis, control flow or field meanings inferred.',
                         'Global pointer arithmetic without a known type stays in unresolved units.',
                         'Dynamic indices are separate from fixed fields; class ownership follows method names.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'imperialism_named.c')
    parser.add_argument('--classes', type=Path, default=ROOT / 'classes.tsv')
    parser.add_argument('--object')
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'fields.tsv')
    args = parser.parse_args()
    with args.classes.open(encoding='utf-8', newline='') as source:
        classes = {row['class']: int(row['size']) for row in csv.DictReader(source, delimiter='\t')}
    report = mine(args.source.read_text(encoding='utf-8'), classes, args.object)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ['object', 'offset', 'width', 'offset_kind', 'dynamic', 'path_resolved',
              'provenance', 'reads', 'writes', 'addresses', 'functions',
              'allocation_size', 'within_allocation']
    with args.output.open('w', encoding='utf-8', newline='') as destination:
        writer = csv.DictWriter(destination, fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        for row in report['result']['rows']:
            writer.writerow(dict(row, offset=hex(row['offset']), functions=','.join(row['functions'])))
    rows = report['result'].pop('rows')
    report['result'].update(output=str(args.output), candidate_rows=len(rows),
                            objects=len({row['object'] for row in rows}),
                            unresolved_rows=sum(row['offset_kind'] != 'bytes' or not row['path_resolved'] for row in rows),
                            dynamic_rows=sum(row['dynamic'] for row in rows),
                            outside_allocation_rows=sum(row['within_allocation'] is False for row in rows))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
