"""TEST FIXTURE ONLY: read or move the turn at which a tech is released (TTechMgr +0x0a + 2*(tech-3), a short; FUN_005af330 draws it
at game start from the year windows, see tools/dump_techtable.py). Usage: python -I poke_techturn.py            (print all)
                                                                          python -I poke_techturn.py 4 25        (tech 4 released on turn 25)"""
import ctypes, struct, sys, importlib.util, os
spec = importlib.util.spec_from_file_location('pt', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poke_tech.py'))
sys.argv, argv = [sys.argv[0]], sys.argv[1:]          # poke_tech runs its argument loop at import: give it none
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)
obj, k32, h = pt.obj, pt.k32, pt.h
def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t(); assert k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)); return b.raw
slots = list(struct.unpack('<26h', rd(obj + 0x0a, 52)))
if argv:
    t, turn = int(argv[0]), int(argv[1]); assert 3 <= t <= 28
    k32.WriteProcessMemory(h, ctypes.c_void_p(obj + 0x0a + 2 * (t - 3)), struct.pack('<h', turn), 2, ctypes.byref(ctypes.c_size_t()))
    print('tech %d release turn %d -> %d' % (t, slots[t - 3], turn))
else:
    for i, s in enumerate(slots): print('tech', i + 3, 'turn', s)
