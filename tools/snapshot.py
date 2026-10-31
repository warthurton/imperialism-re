# Usage: python -I tools/snapshot.py results/snapshot_before.json [--pid PID]
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import subprocess
from datetime import datetime, timezone

# Allocation sizes checked against classes.tsv and TCity initialization at 0x4b24b0.
ORDER_SIZES = {
    0x64fa18: 76, 0x64f7f0: 76, 0x64f958: 84, 0x64f620: 76,
    0x64f848: 80, 0x64f738: 76, 0x64f798: 76, 0x64f8a0: 92,
    0x64f678: 84, 0x64f6d8: 84, 0x64f8f8: 84,
}


class ProcessMemory:
    def __init__(self, pid):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                                 ctypes.c_void_p, ctypes.c_size_t,
                                                 ctypes.POINTER(ctypes.c_size_t)]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.kernel.OpenProcess(0x410, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def read(self, address, size):
        buffer = ctypes.create_string_buffer(size)
        count = ctypes.c_size_t()
        if not self.kernel.ReadProcessMemory(self.handle, address, buffer, size,
                                             ctypes.byref(count)) or count.value != size:
            raise OSError('incomplete memory read at 0x%x (%d bytes)' % (address, size))
        return buffer.raw

    def close(self):
        self.kernel.CloseHandle(self.handle)


def capture(read):
    blocks = {}
    fields = {}

    def pointer(address):
        return struct.unpack('<I', read(address, 4))[0]

    def block(name, address, size):
        if not address:
            raise ValueError('null pointer for ' + name)
        raw = read(address, size)
        blocks[name] = {'address': address, 'size': size, 'hex': raw.hex()}
        return raw

    def field(name, raw, offset, format_string):
        fields[name] = struct.unpack_from('<' + format_string, raw, offset)[0]

    # g_Game is the 0x118-byte TSimMgr allocation (0x49ded0, 0x57b9e0).
    game = pointer(0x6a20f8)
    game_raw = block('game', game, 0x118)
    field('game.turn', game_raw, 0x2c, 'h')
    field('game.local_power', game_raw, 0x2e, 'h')
    field('game.phase', game_raw, 4, 'I')
    if not 0 <= fields['game.local_power'] < 7:
        raise ValueError('expected a loaded single-player game with a local Great Power')
    # Two distinct global LCG states occur in the decompile, with the same multiplier.
    for address in (0x6a38e8, 0x6a5aec):
        raw = block('rng.%08x' % address, address, 4)
        field('rng.seed_%08x' % address, raw, 0, 'I')
    for index in range(23):
        nation = pointer(0x6a4310 + index * 4)
        if not nation:
            continue
        size = 2928 if pointer(nation) == 0x654088 else (2404 if index < 7 else 732)
        raw = block('nation.%d' % index, nation, size)
        field('nation.%d.cash' % index, raw, 0x10, 'i')
        if index >= 7:
            continue
        city = pointer(nation + 0x894)
        if not city:
            continue
        city_raw = block('city.%d' % index, city, 724)
        field('city.%d.turn' % index, city_raw, 0xc, 'h')
        for slot in range(23):
            field('city.%d.stock.%d' % (index, slot), city_raw, 0xb6 + slot * 2, 'h')
        for slot in range(7):
            field('city.%d.capacity.%d' % (index, slot), city_raw, 0x1dc + slot * 2, 'h')
            field('city.%d.capacity_left.%d' % (index, slot), city_raw, 0x1fc + slot * 2, 'h')
        labor = pointer(city + 0x1d8)
        if labor:
            population_raw = block('city.%d.population' % index, labor, 80)
            for name, offset in [('untrained', 0x10), ('trained', 0x14), ('expert', 0x18)]:
                pool = pointer(labor + offset)
                if pool:
                    pool_raw = block('city.%d.pool.%s' % (index, name), pool, 12)
                    field('city.%d.workers.%s' % (index, name), pool_raw, 4, 'h')
            field('city.%d.labor_available' % index, population_raw, 0x1c, 'h')
            field('city.%d.labor_used' % index, population_raw, 0x1e, 'h')
        for slot in range(61):
            order = pointer(city + 0xe4 + slot * 4)
            if order:
                vtable = pointer(order)
                if vtable not in ORDER_SIZES:
                    raise ValueError('unknown order vtable 0x%x at city %d slot %d' % (vtable, index, slot))
                order_raw = block('city.%d.order.%d' % (index, slot), order, ORDER_SIZES[vtable])
                field('city.%d.order.%d.amount' % (index, slot), order_raw, 4, 'h')
    diplomacy = block('diplomacy', pointer(0x6a43d0), 6364)
    for name, offset in [('relation', 0x79c), ('status', 0xbbe),
                         ('turn', 0xfe0), ('presence', 0x1402)]:
        for row in range(23):
            for column in range(23):
                field('diplomacy.%s.%d.%d' % (name, row, column), diplomacy,
                      offset + (row * 23 + column) * 2, 'h')
    technology = block('technology', pointer(0x6a43d8), 0x63c)
    for tech in range(29):
        field('technology.known.%d' % tech, technology, 0x180 + tech, 'B')
        for power in range(7):
            field('technology.power.%d.%d' % (power, tech), technology,
                  0x268 + power * 29 + tech, 'B')
    for tech in range(3, 29):
        field('technology.release_turn.%d' % tech, technology, 0xa + (tech - 3) * 2, 'h')
    trade_address = pointer(0x6a43cc)
    trade = block('trade', trade_address, 2800)
    for commodity in range(17):
        row_offset = 8 + commodity * 160
        for name, offset in [('old_price', 0), ('price', 2), ('buyer_count', 4),
                             ('seller_count', 6), ('total_supply', 0x10), ('base_price', 0x12)]:
            field('trade.%d.%s' % (commodity, name), trade, row_offset + offset, 'h')
        for nation in range(23):
            for name, offset in [('offer', 0x14), ('total', 0x42)]:
                field('trade.%d.%s.%d' % (commodity, name, nation), trade,
                      row_offset + offset + nation * 2, 'h')
        # TDealList owns an array of pointers to 16-byte deal records, not packed records.
        deal_list = pointer(trade_address + 0xaa8 + commodity * 4)
        if deal_list:
            header = block('trade.%d.deals' % commodity, deal_list, 24)
            count, capacity = struct.unpack_from('<ii', header, 8)
            record_size = struct.unpack_from('<h', header, 0x14)[0]
            if not 0 <= count <= capacity <= 100000 or record_size != 16:
                raise ValueError('invalid deal list bounds for commodity %d' % commodity)
            fields['trade.%d.deal_count' % commodity] = count
            if count:
                entries = block('trade.%d.deal_pointers' % commodity, pointer(deal_list + 4), count * 4)
                for index, (address,) in enumerate(struct.iter_unpack('<I', entries)):
                    block('trade.%d.deal.%d' % (commodity, index), address, record_size)
    map_manager = pointer(0x6a43d4)
    block('map_manager', map_manager, 40)
    block('map_tiles', pointer(map_manager + 0xc), 6480 * 0x24)
    block('map_provinces', pointer(map_manager + 0x10), 384 * 0xa8)
    if read(game + 0x2c, 2) != game_raw[0x2c:0x2e]:
        raise RuntimeError('turn changed during capture; retry at an idle map screen')
    return {'result': {'schema': 1, 'blocks': blocks, 'fields': fields},
            'status': 'ok', 'errors': [], 'warnings': [
                'Live reads are not atomic; capture only while the game is idle.',
                'Partial state: game, nations including known AI tails, cities/orders/population/pools, '
                'diplomacy, technology, trade/deals, map manager/tiles/provinces and RNG. '
                'Military objects, province pointer targets, city auxiliary objects and other managers '
                'are not captured.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--pid', type=int)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; choose a new filename')
    pid = args.pid
    if pid is None:
        helper = Path(__file__).resolve().parents[1] / 'harness' / 'prod_pid.ps1'
        processes = subprocess.check_output(['powershell.exe', '-NoProfile', '-ExecutionPolicy',
                                             'Bypass', '-File', str(helper)]).split()
        if len(processes) != 1:
            parser.error('expected exactly one live Imperialism process; found %d' % len(processes))
        pid = int(processes[0])
    memory = ProcessMemory(pid)
    try:
        report = capture(memory.read)
    finally:
        memory.close()
    report['result'].update(pid=pid, captured_at=datetime.now(timezone.utc).isoformat())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
    print(json.dumps({'status': 'ok', 'output': str(args.output),
                      'blocks': len(report['result']['blocks']),
                      'fields': len(report['result']['fields']), 'warnings': report['warnings']}))


if __name__ == '__main__':
    main()
