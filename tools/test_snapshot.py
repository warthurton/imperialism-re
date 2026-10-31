# Usage: python -I tools/test_snapshot.py
import copy
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot import capture, ORDER_SIZES
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
