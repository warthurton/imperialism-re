/*
 * Replacement code for GOG's winmm.dll buffer-recycle blocks.
 *
 * Original (three copies, racy against the playback thread):
 *     unprepare(hwo, slot[i], 0x20);
 *     free(slot[i]->lpData);     // slot[i] re-read here: may already be NULL  -> crash
 *     free(slot[i]);             // ... or already freed by the other thread   -> double free
 *     slot[i] = NULL;
 *
 * Replacement: claim the slot atomically *for the buffer that was tested*, and only the
 * thread that wins the claim touches it:
 *     if (cmpxchg(&slot[i], expected = p, 0) != p) goto resume;   // someone else took it
 *     unprepare(hwo, p, 0x20); free(p->lpData); free(p);
 *
 * Entry:  eax = p (non-NULL, WHDR_DONE seen), ebx = i, edx possibly live (preserved).
 * Exit:   jumps to the original loop's continuation with ESP exactly as on entry.
 * The pushes/pops balance: stdcall unprepare pops its own 12 bytes, cdecl free is cleaned here.
 * Included by both shim.c and cavetest.c so what is tested is what ships.
 */
#ifndef WINMM_CAVE_H
#define WINMM_CAVE_H

static BYTE *wc_bytes(BYTE *p, const void *b, unsigned n)
{
    memcpy(p, b, n);
    return p + n;
}
static BYTE *wc_u32(BYTE *p, DWORD v)
{
    memcpy(p, &v, 4);
    return p + 4;
}
/* rel32 forms: the displacement is relative to the end of the instruction (= end of rel32) */
static BYTE *wc_rel(BYTE *p, const void *opcode, unsigned oplen, DWORD target)
{
    p = wc_bytes(p, opcode, oplen);
    return wc_u32(p, target - (DWORD)(ULONG_PTR)(p + 4));
}

/* Emits one cave at p; returns the number of bytes written. */
static unsigned wc_build(BYTE *p, DWORD table, DWORD hwo, DWORD unprep, DWORD freefn, DWORD resume,
                         DWORD counter_ok, DWORD counter_skip)
{
    BYTE *start = p, *jne_fix;
    static const BYTE xor_ecx[]      = { 0x33, 0xC9 };
    static const BYTE lock_cmpxchg[] = { 0xF0, 0x0F, 0xB1, 0x0C, 0x9D };   /* [4*ebx+disp32], ecx */
    static const BYTE jne32[]        = { 0x0F, 0x85 };
    static const BYTE push_edx[]     = { 0x52 };
    static const BYTE push_eax[]     = { 0x50 };
    static const BYTE push_20[]      = { 0x6A, 0x20 };
    static const BYTE push_hwo[]     = { 0xFF, 0x35 };                       /* push dword [abs] */
    static const BYTE call32[]       = { 0xE8 };
    static const BYTE mov_eax_esp[]  = { 0x8B, 0x04, 0x24 };
    static const BYTE push_peax[]    = { 0xFF, 0x30 };                       /* push dword [eax] */
    static const BYTE add_esp4[]     = { 0x83, 0xC4, 0x04 };
    static const BYTE push_pesp[]    = { 0xFF, 0x34, 0x24 };                 /* push dword [esp] */
    static const BYTE pop_edx[]      = { 0x5A };
    static const BYTE lock_inc[]     = { 0xF0, 0xFF, 0x05 };                 /* lock inc dword [abs] */
    static const BYTE jmp32[]        = { 0xE9 };

    p = wc_bytes(p, xor_ecx, sizeof xor_ecx);
    p = wc_bytes(p, lock_cmpxchg, sizeof lock_cmpxchg);
    p = wc_u32(p, table);
    p = wc_bytes(p, jne32, sizeof jne32);            /* jne skip (fixed up below) */
    jne_fix = p;
    p = wc_u32(p, 0);
    p = wc_bytes(p, push_edx, 1);                    /* save edx */
    p = wc_bytes(p, push_eax, 1);                    /* save p   */
    p = wc_bytes(p, push_20, 2);                     /* unprepare(hwo, p, 0x20) */
    p = wc_bytes(p, push_eax, 1);
    p = wc_bytes(p, push_hwo, 2);
    p = wc_u32(p, hwo);
    p = wc_rel(p, call32, 1, unprep);                /* stdcall: pops its 12 bytes */
    p = wc_bytes(p, mov_eax_esp, 3);                 /* eax = saved p */
    p = wc_bytes(p, push_peax, 2);                   /* free(p->lpData) */
    p = wc_rel(p, call32, 1, freefn);
    p = wc_bytes(p, add_esp4, 3);
    p = wc_bytes(p, push_pesp, 3);                   /* free(p) */
    p = wc_rel(p, call32, 1, freefn);
    p = wc_bytes(p, add_esp4, 3);
    p = wc_bytes(p, add_esp4, 3);                    /* drop saved p */
    p = wc_bytes(p, pop_edx, 1);                     /* restore edx */
    p = wc_bytes(p, lock_inc, 3);
    p = wc_u32(p, counter_ok);
    p = wc_rel(p, jmp32, 1, resume);
    /* skip: another thread owns (or already recycled) this slot */
    {
        DWORD skip_va = (DWORD)(ULONG_PTR)p;
        DWORD rel = skip_va - (DWORD)(ULONG_PTR)(jne_fix + 4);
        memcpy(jne_fix, &rel, 4);
    }
    p = wc_bytes(p, lock_inc, 3);
    p = wc_u32(p, counter_skip);
    p = wc_rel(p, jmp32, 1, resume);
    return (unsigned)(p - start);
}

#endif
