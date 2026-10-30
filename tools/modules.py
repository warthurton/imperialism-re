"""List the modules loaded in the running (32-bit) Imperialism.exe, optionally filtered by a substring."""
import ctypes, ctypes.wintypes as wt, subprocess, sys
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process $env:PROC).Id']).split()[0])
k32 = ctypes.WinDLL('kernel32', use_last_error=True); psapi = ctypes.WinDLL('psapi', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
mods = (ctypes.c_void_p * 1024)(); need = wt.DWORD()
assert psapi.EnumProcessModulesEx(h, mods, ctypes.sizeof(mods), ctypes.byref(need), 0x03), 'EnumProcessModulesEx failed'
flt = sys.argv[1].lower() if len(sys.argv) > 1 else ''
for i in range(need.value // ctypes.sizeof(ctypes.c_void_p)):
    buf = ctypes.create_unicode_buffer(520)
    psapi.GetModuleFileNameExW(h, ctypes.c_void_p(mods[i]), buf, 520)
    if flt in buf.value.lower(): print(buf.value)
