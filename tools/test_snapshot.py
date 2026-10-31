# Usage: python -I tools/test_snapshot.py
import copy
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot import capture, ORDER_SIZES, TASK_SIZES
from diff_snapshot import compare


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.regions = {}
        self.next_address = 0x100000
        self.allocate(0x5000, address=0x6a1000)
        self.game = self.allocate(0x118, 0x6a20f8)
        self.nations = []
        for index in range(23):
            self.nations.append(self.allocate(2928 if index == 1 else (2404 if index < 7 else 732),
                                              0x6a4310 + index * 4))
        self.write(self.nations[1], struct.pack('<I', 0x654088))
        self.city = self.allocate(724, self.nations[0] + 0x894)
        population = self.allocate(80, self.city + 0x1d8)
        for offset in (0x10, 0x14, 0x18):
            self.allocate(12, population + offset)
        self.orders = []
        for index, (vtable, size) in enumerate(ORDER_SIZES.items()):
            order = self.allocate(size, self.city + 0xe4 + index * 4)
            self.write(order, struct.pack('<I', vtable))
            self.orders.append(order)
        self.allocate(6364, 0x6a43d0)
        self.allocate(0x63c, 0x6a43d8)
        trade = self.allocate(2800, 0x6a43cc)
        self.deal_list = self.allocate(24, trade + 0xaa8)
        self.write(self.deal_list + 0x14, struct.pack('<h', 16))
        manager = self.allocate(40, 0x6a43d4)
        self.allocate(6480 * 0x24, manager + 0xc)
        self.allocate(384 * 0xa8, manager + 0x10)
        self.task_list = self.allocate(32, self.city + 0x270)
        self.write(self.task_list, struct.pack('<I', 0x66aa48))
        self.auxiliary = self.allocate(24, self.city + 0x274)
        self.write(self.auxiliary + 0x14, struct.pack('<h', 4))

    def allocate(self, size, pointer=None, address=None):
        if address is None:
            address = self.next_address
            self.next_address += size + 0x100
        self.regions[address] = bytearray(size)
        if pointer is not None:
            self.write(pointer, struct.pack('<I', address))
        return address

    def write(self, address, data):
        for base, region in self.regions.items():
            if base <= address and address + len(data) <= base + len(region):
                region[address - base:address - base + len(data)] = data
                return
        raise OSError('unmapped write')

    def read(self, address, size):
        for base, region in self.regions.items():
            if base <= address and address + size <= base + len(region):
                return bytes(region[address - base:address - base + size])
        raise OSError('unmapped read: %x size %d' % (address, size))

    def test_economic_change_and_identity(self):
        before = capture(self.read)
        self.assertTrue(compare(before, before)['result']['equal'])
        self.write(self.city + 0xb6, struct.pack('<h', 42))
        self.write(self.nations[0] + 0x10, struct.pack('<i', -500))
        after = capture(self.read)
        changes = compare(before, after, True)['result']
        self.assertEqual({change['field'] for change in changes['fields']},
                         {'city.0.stock.0', 'nation.0.cash'})
        self.assertEqual(len(changes['blocks']), 2)
        self.assertEqual(len(bytes.fromhex(after['result']['blocks']['map_tiles']['hex'])),
                         6480 * 0x24)

    def test_missing_pointer_fails(self):
        self.write(0x6a43d8, bytes(4))
        with self.assertRaisesRegex(ValueError, 'technology'):
            capture(self.read)

    def test_variable_allocations_and_unit_tail(self):
        before = capture(self.read)
        self.assertEqual(before['result']['blocks']['nation.1']['size'], 2928)
        for index, size in enumerate(ORDER_SIZES.values()):
            self.assertEqual(before['result']['blocks']['city.0.order.%d' % index]['size'], size)
        unit_index = list(ORDER_SIZES).index(0x64f8a0)
        self.write(self.orders[unit_index] + 90, struct.pack('<h', 123))
        changes = compare(before, capture(self.read), True)['result']
        self.assertEqual(changes['blocks'][0]['bytes'][0]['offset'], 90)

    def test_unknown_order_fails(self):
        self.write(self.orders[0], bytes(4))
        with self.assertRaisesRegex(ValueError, 'unknown order vtable'):
            capture(self.read)

    def test_deal_records_follow_pointers(self):
        self.write(self.deal_list + 8, struct.pack('<ii', 1, 1))
        entries = self.allocate(4, self.deal_list + 4)
        record = self.allocate(16, entries)
        self.write(record + 12, struct.pack('<h', 5))
        state = capture(self.read)['result']
        self.assertEqual(state['blocks']['trade.0.deal.0']['address'], record)
        self.assertEqual(state['fields']['trade.0.deal_count'], 1)
        self.write(self.deal_list + 8, struct.pack('<i', 2))
        with self.assertRaisesRegex(ValueError, 'invalid deal list bounds'):
            capture(self.read)

    def test_task_chain_allocation_and_cycle_rejection(self):
        nodes = [self.allocate(12), self.allocate(12)]
        self.write(self.task_list + 8, struct.pack('<IIi', nodes[0], nodes[1], 2))
        for slot, (vtable, size) in enumerate(TASK_SIZES.items()):
            task = self.allocate(size)
            self.write(task, struct.pack('<I', vtable))
            self.write(nodes[slot], struct.pack('<III', nodes[1] if slot == 0 else 0,
                                               nodes[0] if slot == 1 else 0, task))
        state = capture(self.read)['result']
        self.assertEqual(state['fields']['city.0.task_count'], 2)
        self.assertEqual([state['blocks']['city.0.task.%d' % slot]['size'] for slot in range(2)], [20, 24])
        self.write(nodes[1], struct.pack('<I', nodes[0]))
        with self.assertRaisesRegex(ValueError, 'count/tail mismatch'):
            capture(self.read)

    def test_city_auxiliary_records_follow_pointers(self):
        self.write(self.auxiliary + 8, struct.pack('<ii', 1, 1))
        entries = self.allocate(4, self.auxiliary + 4)
        record = self.allocate(4, entries)
        self.write(record, struct.pack('<hh', 3, 5))
        state = capture(self.read)['result']
        self.assertEqual(state['blocks']['city.0.auxiliary_record.0']['hex'], '03000500')
        self.write(self.auxiliary + 0x14, struct.pack('<h', 8))
        with self.assertRaisesRegex(ValueError, 'auxiliary record bounds'):
            capture(self.read)

    def test_minister_standard_and_embedded_lists(self):
        minister = self.allocate(452, self.nations[0] + 0x98)
        self.write(minister, struct.pack('<I', 0x6508a8))
        for offset, embedded in ((0x2c, 0), (0x18c, 4)):
            header = self.allocate(28 + embedded, minister + offset)
            node = self.allocate(12)
            self.write(header + embedded + 4, struct.pack('<IIi', node, node, 1))
            self.write(node, struct.pack('<III', 0, 0, 7))
        state = capture(self.read)['result']
        self.assertEqual(state['fields']['nation.0.interior.list_02c.count'], 1)
        self.assertEqual(state['fields']['nation.0.interior.list_18c.count'], 1)

    def test_province_army_unit_chain(self):
        manager = struct.unpack('<I', self.read(0x6a43d4, 4))[0]
        provinces = struct.unpack('<I', self.read(manager + 0x10, 4))[0]
        unit = self.allocate(68, provinces + 0x98)
        self.write(unit, struct.pack('<I', 0x66eea8))
        state = capture(self.read)['result']
        self.assertEqual(state['fields']['army.unit_count'], 1)
        self.assertEqual(state['blocks']['province.0.unit.0']['size'], 68)
        self.write(unit + 0x14, struct.pack('<I', unit))
        with self.assertRaisesRegex(ValueError, 'province military chain'):
            capture(self.read)

    def test_army_record_bounds(self):
        army = self.allocate(936, 0x6a3338)
        self.write(army, struct.pack('<I', 0x64c928))
        records = self.allocate(24, army + 4)
        self.write(records + 8, struct.pack('<ii', 1, 1))
        self.write(records + 0x14, struct.pack('<h', 0x268))
        entries = self.allocate(4, records + 4)
        self.allocate(0x268, entries)
        self.assertEqual(capture(self.read)['result']['fields']['army.record_count'], 1)
        self.write(records + 0x14, struct.pack('<h', 4))
        with self.assertRaisesRegex(ValueError, 'army record bounds'):
            capture(self.read)

    def test_stack_nodes_and_nation_roster_share_unit(self):
        army = self.allocate(936, 0x6a3338)
        self.write(army, struct.pack('<I', 0x64c928))
        header = self.allocate(32, army + 0xc)
        stack_node = self.allocate(12)
        stack = self.allocate(28)
        self.write(header + 8, struct.pack('<IIi', stack_node, stack_node, 1))
        self.write(stack_node, struct.pack('<III', 0, 0, stack))
        self.write(stack, struct.pack('<I', 0x64ca38))
        self.write(stack + 10, struct.pack('<h', 1))
        node = self.allocate(8, stack + 0x14)
        unit = self.allocate(68)
        self.write(unit, struct.pack('<I', 0x66eea8))
        self.write(node, struct.pack('<II', unit, 0))
        roster = self.allocate(32, self.nations[0] + 0x44)
        roster_node = self.allocate(12)
        self.write(roster + 8, struct.pack('<IIi', roster_node, roster_node, 1))
        self.write(roster_node, struct.pack('<III', 0, 0, unit))
        state = capture(self.read)['result']
        self.assertEqual(state['fields']['army.unit_count'], 1)
        self.assertEqual(state['fields']['army.stack_count'], 1)
        self.assertEqual(state['fields']['army.unlisted_unit_count'], 0)
        self.assertEqual(state['fields']['army.unplaced_unit_count'], 0)
        self.assertEqual(state['blocks']['army.stack.0.unit.0']['address'], unit)
        self.write(node + 4, struct.pack('<I', node))
        with self.assertRaisesRegex(ValueError, 'army stack count mismatch'):
            capture(self.read)

    def test_roster_only_and_province_only_units_are_reported(self):
        manager = struct.unpack('<I', self.read(0x6a43d4, 4))[0]
        provinces = struct.unpack('<I', self.read(manager + 0x10, 4))[0]
        placed = self.allocate(68, provinces + 0x98)
        self.write(placed, struct.pack('<I', 0x66eea8))
        roster = self.allocate(32, self.nations[0] + 0x44)
        node = self.allocate(12)
        unplaced = self.allocate(68)
        self.write(unplaced, struct.pack('<I', 0x66eea8))
        self.write(roster + 8, struct.pack('<IIi', node, node, 1))
        self.write(node, struct.pack('<III', 0, 0, unplaced))
        state = capture(self.read)['result']
        self.assertEqual(state['fields']['army.unit_count'], 2)
        self.assertEqual(state['fields']['army.unlisted_unit_count'], 1)
        self.assertEqual(state['fields']['army.unplaced_unit_count'], 1)
        self.assertEqual(state['blocks']['nation.0.military.unit.0']['address'], unplaced)

    def test_unknown_graph_types_rejected_before_full_read(self):
        for root, message in ((0x6a3338, 'army manager'), (0x6a43e4, 'navy manager'),
                              (0x6a3edc, 'ship vtable')):
            with self.subTest(root=root):
                self.allocate(4, root)
                with self.assertRaisesRegex(ValueError, message):
                    capture(self.read)
                self.write(root, bytes(4))

    def test_intrusive_ship_chain_and_cycle(self):
        navy = self.allocate(16, 0x6a43e4)
        self.write(navy, struct.pack('<I', 0x65c4c8))
        ships = [self.allocate(56, 0x6a3edc), self.allocate(56)]
        for index, ship in enumerate(ships):
            self.write(ship, struct.pack('<I', 0x65c438))
            self.write(ship + 0x24, struct.pack('<II', ships[1] if index == 0 else 0,
                                              ships[0] if index == 1 else 0))
        self.assertEqual(capture(self.read)['result']['fields']['navy.ship_count'], 2)
        self.write(ships[1] + 0x24, struct.pack('<I', ships[0]))
        with self.assertRaisesRegex(ValueError, 'global ship chain'):
            capture(self.read)

    def test_turn_change_fails(self):
        def advancing_read(address, size):
            if address == self.game + 0x2c:
                return struct.pack('<h', 1)
            return self.read(address, size)

        with self.assertRaisesRegex(RuntimeError, 'turn changed'):
            capture(advancing_read)

    def test_removed_block_and_schema(self):
        before = capture(self.read)
        after = copy.deepcopy(before)
        del after['result']['blocks']['city.0.order.0']
        changes = compare(before, after)['result']
        self.assertEqual(changes['blocks'][0]['change'], 'removed')
        after['result']['schema'] = 2
        with self.assertRaises(ValueError):
            compare(before, after)

    def test_diff_cli_exit_codes_and_limit(self):
        import json
        state = capture(self.read)
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / 'before.json', Path(directory) / 'after.json'
            before.write_text(json.dumps(state))
            after.write_text(json.dumps(state))
            command = [sys.executable, '-I', str(Path(__file__).with_name('diff_snapshot.py')),
                       str(before), str(after), '--limit', '0']
            equal = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(equal.returncode, 0, equal.stderr)
            state['result']['fields']['game.turn'] += 1
            after.write_text(json.dumps(state))
            changed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(changed.returncode, 1, changed.stderr)
            result = json.loads(changed.stdout)['result']
            self.assertEqual(result['field_change_count'], 1)
            self.assertEqual(result['fields'], [])


if __name__ == '__main__':
    unittest.main()
