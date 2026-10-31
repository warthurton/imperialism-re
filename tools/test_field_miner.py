# Usage: python -I tools/test_field_miner.py
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from field_miner import mine, mine_function


class FieldMinerTests(unittest.TestCase):
    def accesses(self, statements, signature='int *param_1', name='TExample_vf9'):
        body = 'void __thiscall example(' + signature + ') { ' + statements + ' }'
        return mine_function(name, 0x500000, body, {'TExample'})

    def test_pointer_scaling_and_cast_order(self):
        rows = self.accesses('*(short *)(param_1 + 3) = 1; '
                             '*(short *)((int)param_1 + 3) = 2; '
                             '*(short *)((short *)param_1 + 3) = 3;')
        self.assertEqual([(row['offset'], row['width']) for row in rows], [(12, 2), (3, 2), (6, 2)])

    def test_reads_writes_comparisons_and_increments(self):
        rows = self.accesses('*(int *)(param_1 + 1) = 7; '
                             '*(int *)(param_1 + 2) += 2; '
                             'if (*(int *)(param_1 + 3) == 9) '
                             '++*(int *)(param_1 + 4); '
                             '(*(int *)(param_1 + 5))--;')
        self.assertEqual([row['mode'] for row in rows],
                         ['write', 'read_write', 'read', 'read_write', 'read_write'])

    def test_binary_bitand_does_not_count_as_address_taking(self):
        rows = self.accesses('value = flags & param_1[2]; '
                             'value = flags & *(short *)(param_1 + 4); '
                             'call(&param_1[3]);')
        self.assertEqual([row['mode'] for row in rows], ['read', 'read', 'address'])

    def test_arrays_dynamic_fields_and_address_taking(self):
        rows = self.accesses('param_1[2] = 1; param_1[index] += 1; '
                             'call(&param_1[4]); *(short *)(param_1 + index * 3 + 1) = 2;')
        self.assertEqual([(row['offset'], row['dynamic'], row['mode']) for row in rows],
                         [(8, False, 'write'), (0, True, 'read_write'),
                          (16, False, 'address'), (4, True, 'write')])

    def test_nested_targets_do_not_become_parent_fields(self):
        rows = self.accesses('*(short *)(*(int *)((int)param_1 + 8) + 6) = 5;')
        self.assertEqual([(row['object'], row['offset'], row['width']) for row in rows],
                         [('TExample->+0x8', 6, 2), ('TExample', 8, 4)])

    def test_globals_keep_unknown_scaling_even_after_cast(self):
        rows = self.accesses('*(short *)(g_Unknown + 8) = 1; '
                             '*(short *)((int)(g_Unknown + 8) + 4) = 2; '
                             '*(short *)((int)g_Unknown + 8) = 3;')
        self.assertEqual([row['offset_kind'] for row in rows],
                         ['unknown_stride_units', 'unknown_stride_units', 'bytes'])

    def test_unresolved_parent_path_stays_unresolved(self):
        rows = self.accesses('*(short *)(*(int *)(g_Unknown + 8) + 2) = 3;')
        self.assertFalse(rows[0]['path_resolved'])
        self.assertEqual(rows[0]['object'], 'g_Unknown->+0x8?units')

    def test_negative_offsets_and_comments(self):
        rows = self.accesses('/* *(short *)(param_1 + 999) = 0; */ '
                             'call("*(short *)(param_1 + 888)"); '
                             '*(short *)(param_1 + -2) = 3;')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['offset'], -8)

    def test_static_comparator_is_not_a_class_instance(self):
        rows = mine_function('TExample_vf17', 0x500000,
                             'int compare(short *param_1) { return param_1[3]; }', {'TExample'})
        self.assertTrue(rows[0]['object'].startswith('function.'))

    def test_aggregate_and_skip_link_stubs(self):
        source = ('// TExample_vf8 @ 00401000\n'
                  'void __thiscall demo(int param_1) { *(short *)(param_1 + 12) = 1; }\n'
                  '// TExample_vf9 @ 00500000\n'
                  'void __thiscall demo(int param_1) { *(short *)(param_1 + 12) = 1; '
                  '*(short *)(param_1 + 12) += 2; }\n')
        report = mine(source, {'TExample'})
        row = report['result']['rows'][0]
        self.assertEqual((row['reads'], row['writes']), (1, 2))
        self.assertEqual(row['functions'], ['00500000:TExample_vf9'])
        self.assertNotIn('*(short', json.dumps(report))

    def test_declared_bounds_are_a_check_not_a_larger_allocation(self):
        source = ('// TExample_vf9 @ 00500000\n'
                  'void __thiscall demo(int *param_1) { '
                  '*(short *)(param_1 + 1) = 1; *(short *)(param_1 + 4) = 2; }')
        rows = mine(source, {'TExample': 12})['result']['rows']
        self.assertEqual([row['within_allocation'] for row in rows], [True, False])
        self.assertEqual([row['allocation_size'] for row in rows], [12, 12])


if __name__ == '__main__':
    unittest.main()
