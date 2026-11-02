"""Read-only research helper: find which dwords in the game's own image (0x400000-0x708000, code, data and bss globals) hold given values.
Usage: python -I scan_ptr.py <hex value> [<hex value> ...]       prints address and the value for every dword equal to one of them
Used to find the global that points at the currently selected civilian: scan for my units' addresses, press Next Unit, scan again."""
import ctypes, ctypes.wintypes as wt, struct, subprocess, sys

vals = {int(a, 16) for a in sys.argv[1:]}
pid = int(subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id']).decode().strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True); k32.OpenProcess.restype = wt.HANDLE
h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
base, size = 0x400000, 0x308000
buf = ctypes.create_string_buffer(size); got = ctypes.c_size_t()
k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got))
data = buf.raw[:got.value]
for off in range(0, len(data) - 3, 4):
    v = struct.unpack_from('<I', data, off)[0]
    if v in vals:
        print('%08x = %08x' % (base + off, v))
