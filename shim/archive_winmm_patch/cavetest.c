/* Builds one cave at a fixed fake address and dumps it, so it can be disassembled and
 * checked independently of the shim. Uses the same winmm_cave.h as the shim. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "winmm_sites.h"
#include "winmm_cave.h"

int main(void)
{
    BYTE *buf = (BYTE *)VirtualAlloc(NULL, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    unsigned n = wc_build(buf, WINMM_SLOT_TABLE, WINMM_HWO, WINMM_UNPREP_THUNK, WINMM_FREE_THUNK,
                          WINMM_S1_RESUME, 0x10000000u, 0x10000004u);
    unsigned i;
    printf("cave_va=%08lx len=%u\n", (unsigned long)(ULONG_PTR)buf, n);
    for (i = 0; i < n; i++) printf("%02x ", buf[i]);
    printf("\n");
    return 0;
}
