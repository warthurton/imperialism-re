"""Read-only: print the game's 14 preference shorts (g_Game+0x48+2N) and the turn counter from the running Imperialism.exe."""
import ctypes, ctypes.wintypes as wt, struct, subprocess
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
def rd(a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t(); assert k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(g)); return b.raw
game = struct.unpack('<I', rd(0x6a20f8, 4))[0]
prefs = struct.unpack('<14h', rd(game + 0x48, 28))
print('g_Game turn counter', struct.unpack('<h', rd(game + 0x2c, 2))[0])
for i, v in enumerate(prefs): print('Pref%-2d = %d' % (i, v))
