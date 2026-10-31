# Internal snapshot graph walkers; invoked by tools/snapshot.py.
import struct

MINISTER_SIZES = {0x6508a8: 452, 0x650d30: 452, 0x650e90: 452,
                  0x650bd0: 452, 0x650a70: 452}
LIMIT = 100000


def capture_graph(read, block, fields):
    def pointer(address):
        return struct.unpack('<I', read(address, 4))[0]

    def linked_list(name, address, embedded=0):
        raw = block(name, address, 28 + embedded)
        head, tail, count = struct.unpack_from('<IIi', raw, embedded + 4)
        if not 0 <= count <= LIMIT:
            raise ValueError('invalid count: ' + name)
        fields[name + '.count'] = count
        node, previous, visited, values = head, 0, set(), []
        for index in range(count):
            if not node or node in visited:
                raise ValueError('invalid chain: ' + name)
            visited.add(node)
            raw_node = block(name + '.node.%d' % index, node, 12)
            following, prior, value = struct.unpack('<III', raw_node)
            if prior != previous:
                raise ValueError('invalid back link: ' + name)
            values.append(value)
            previous, node = node, following
        if node or previous != tail:
            raise ValueError('count/tail mismatch: ' + name)
        return values

    for nation_index in range(7):
        nation = pointer(0x6a4310 + nation_index * 4)
        # Great Power initialization 0x4d8cc0 stores Interior at +0x98 (Foreign is +0x94).
        minister = pointer(nation + 0x98) if nation else 0
        if not minister:
            continue
        vtable = pointer(minister)
        if vtable not in MINISTER_SIZES:
            raise ValueError('unknown Interior Minister vtable 0x%x' % vtable)
        name = 'nation.%d.interior' % nation_index
        block(name, minister, MINISTER_SIZES[vtable])
        # 0x4be8d0 allocates three standard 28-byte lists and one 32-byte facade.
        for offset in (0x28, 0x2c, 0x190):
            address = pointer(minister + offset)
            if address:
                linked_list(name + '.list_%03x' % offset, address)
        address = pointer(minister + 0x18c)
        if address:
            linked_list(name + '.list_18c', address, embedded=4)

    army = pointer(0x6a3338)
    stacks = []
    if army:
        if pointer(army) != 0x64c928:
            raise ValueError('unknown army manager vtable')
        block('army', army, 936)
        records = pointer(army + 4)
        if records:
            header = block('army.records', records, 24)
            count, capacity = struct.unpack_from('<ii', header, 8)
            stride = struct.unpack_from('<h', header, 0x14)[0]
            if not 0 <= count <= capacity <= LIMIT or stride != 0x268:
                raise ValueError('invalid army record bounds')
            fields['army.record_count'] = count
            if count:
                entries = block('army.record_pointers', pointer(records + 4), count * 4)
                for index, (address,) in enumerate(struct.iter_unpack('<I', entries)):
                    block('army.record.%d' % index, address, stride)
        stack_list = pointer(army + 0xc)
        if stack_list:
            stacks = linked_list('army.stacks', stack_list, embedded=4)

    map_manager = pointer(0x6a43d4)
    provinces = pointer(map_manager + 0x10)
    units = set()
    for province in range(384):
        # 0x4a1f80 walks MilitaryUnit.next (+0x14) directly from province +0x98.
        unit = pointer(provinces + province * 0xa8 + 0x98)
        previous, visited = 0, set()
        while unit:
            if unit in visited or len(visited) >= LIMIT:
                raise ValueError('invalid province military chain')
            visited.add(unit)
            if pointer(unit) != 0x66eea8:
                raise ValueError('unknown province military unit vtable 0x%x' % pointer(unit))
            raw = block('province.%d.unit.%d' % (province, len(visited) - 1), unit, 68)
            prior, following = struct.unpack_from('<II', raw, 0x10)
            if prior != previous:
                raise ValueError('invalid province military back link')
            units.add(unit)
            previous, unit = unit, following
        if visited:
            fields['province.%d.unit_count' % province] = len(visited)
    for stack_index, stack in enumerate(stacks):
        name = 'army.stack.%d' % stack_index
        if pointer(stack) != 0x64ca38:
            raise ValueError('unknown army stack vtable')
        raw = block(name, stack, 28)
        count = struct.unpack_from('<h', raw, 10)[0]
        if not 0 <= count <= LIMIT:
            raise ValueError('invalid army stack count')
        fields[name + '.unit_count'] = count
        node, visited = pointer(stack + 0x14), set()
        for index in range(count):
            if not node or node in visited:
                raise ValueError('invalid army stack unit chain')
            visited.add(node)
            unit, following = struct.unpack('<II', block(name + '.node.%d' % index, node, 8))
            if pointer(unit) != 0x66eea8:
                raise ValueError('unknown military unit vtable')
            block(name + '.unit.%d' % index, unit, 68)
            units.add(unit)
            node = following
        if node:
            raise ValueError('army stack count mismatch')
    fields['army.stack_count'] = len(stacks)
    placed_units, roster_units = set(units), set()
    for nation_index in range(23):
        nation = pointer(0x6a4310 + nation_index * 4)
        roster = pointer(nation + 0x44) if nation else 0
        if not roster:
            continue
        name = 'nation.%d.military' % nation_index
        for index, unit in enumerate(linked_list(name, roster, embedded=4)):
            if pointer(unit) != 0x66eea8:
                raise ValueError('unknown nation military unit vtable')
            roster_units.add(unit)
            if unit not in units:
                block(name + '.unit.%d' % index, unit, 68)
                units.add(unit)
    fields['army.unit_count'] = len(units)
    fields['army.unlisted_unit_count'] = len(placed_units - roster_units)
    fields['army.unplaced_unit_count'] = len(roster_units - placed_units)

    navy = pointer(0x6a43e4)
    if navy:
        if pointer(navy) != 0x65c4c8:
            raise ValueError('unknown navy manager vtable')
        block('navy', navy, 16)
    # 0x54f500 and 0x556ad0 establish the intrusive ship chain and its links.
    ship, previous, visited = pointer(0x6a3edc), 0, set()
    while ship:
        if ship in visited or len(visited) >= LIMIT:
            raise ValueError('invalid global ship chain')
        visited.add(ship)
        if pointer(ship) != 0x65c438:
            raise ValueError('unknown ship vtable')
        raw = block('navy.ship.%d' % (len(visited) - 1), ship, 56)
        following, prior = struct.unpack_from('<II', raw, 0x24)
        if prior != previous:
            raise ValueError('invalid ship back link')
        previous, ship = ship, following
    fields['navy.ship_count'] = len(visited)
