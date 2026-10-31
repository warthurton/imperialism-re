/* trace_calls: coverage and call-edge tracer for the 32-bit Imperialism.exe (attaches to a running game, patches INT3 at function entries).
 *
 * usage: trace_calls <pid> <funclist.txt> <outprefix> [--seconds N] [--cap N] [--phase-fn HEXADDR]
 *   funclist.txt   one function per line: a hex address (0x optional), anything after it is ignored (tools/tracer/make_funclist.py writes it)
 *   --seconds N    stop after N seconds (default 60) or when the file <outprefix>.stop appears
 *   --cap N        a function stops being traced after N hits (default 100): hot functions would make the game crawl
 *   --phase-fn A   the turn driver (default 0x57da70 = TSimMgr_AdvancePhase): on every hit, ECX is read as `this` and the DWORD at this+4 is taken as the
 *                  current phase; every later hit is tagged with it (bit mask)
 * writes <outprefix>_funcs.tsv  (addr, hits, first_seq, phase_mask, first_caller_function, capped) and <outprefix>_edges.tsv (caller, callee, count).
 * At the end every breakpoint is removed and the process is detached, so the game keeps running.
 *
 * Build: i686-w64-mingw32-clang -O2 -Wall -static -o trace_calls.exe trace_calls.c      (the game is 32-bit; so is this program)
 * Limits: a thread that runs through a function while its first byte is being restored for the single step is missed; only entries are traced, not returns.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    DWORD addr;
    DWORD hits, first_seq, phases, first_caller;
    BYTE orig;
    BYTE armed;      /* breakpoint currently written */
    BYTE disabled;   /* reached the cap */
} Fn;

static Fn *fns;
static int nfn;

typedef struct { DWORD caller, callee, count; } Edge;
#define EDGE_BITS 20
static Edge *edges;

typedef struct { DWORD tid; int fn; } Pending;
static Pending pending[256];

static int find_fn(DWORD addr)      /* exact */
{
    int lo = 0, hi = nfn - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (fns[mid].addr == addr) return mid;
        if (fns[mid].addr < addr) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

static int containing_fn(DWORD addr)  /* the function whose entry is the largest <= addr */
{
    int lo = 0, hi = nfn - 1, best = -1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (fns[mid].addr <= addr) { best = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return best;
}

static int cmp(const void *a, const void *b)
{
    DWORD x = ((const Fn *)a)->addr, y = ((const Fn *)b)->addr;
    return x < y ? -1 : x > y;
}

static void add_edge(DWORD caller, DWORD callee)
{
    DWORD h = (caller * 2654435761u ^ callee * 40503u) & ((1u << EDGE_BITS) - 1);
    for (int i = 0; i < 64; i++) {
        Edge *e = &edges[(h + i) & ((1u << EDGE_BITS) - 1)];
        if (e->count == 0) { e->caller = caller; e->callee = callee; e->count = 1; return; }
        if (e->caller == caller && e->callee == callee) { e->count++; return; }
    }
}

static HANDLE proc;

static void put_byte(DWORD addr, BYTE b)
{
    SIZE_T n;
    WriteProcessMemory(proc, (LPVOID)addr, &b, 1, &n);
    FlushInstructionCache(proc, (LPVOID)addr, 1);
}

int main(int argc, char **argv)
{
    if (argc < 4) { fprintf(stderr, "usage: trace_calls <pid> <funclist> <outprefix> [--seconds N] [--cap N] [--phase-fn HEX]\n"); return 2; }
    DWORD pid = (DWORD)atoi(argv[1]);
    const char *list = argv[2], *prefix = argv[3];
    int seconds = 60, cap = 100;
    DWORD phase_fn = 0x57da70;
    for (int i = 4; i + 1 < argc; i += 2) {
        if (!strcmp(argv[i], "--seconds")) seconds = atoi(argv[i + 1]);
        else if (!strcmp(argv[i], "--cap")) cap = atoi(argv[i + 1]);
        else if (!strcmp(argv[i], "--phase-fn")) phase_fn = (DWORD)strtoul(argv[i + 1], NULL, 16);
    }
    FILE *f = fopen(list, "r");
    if (!f) { perror("funclist"); return 2; }
    int capn = 16384;
    fns = calloc(capn, sizeof(Fn));
    char line[512];
    while (fgets(line, sizeof line, f)) {
        DWORD a = (DWORD)strtoul(line, NULL, 16);
        if (a < 0x401000 || a > 0x640000) continue;
        if (nfn == capn) { capn *= 2; fns = realloc(fns, capn * sizeof(Fn)); }
        fns[nfn++].addr = a;
    }
    fclose(f);
    qsort(fns, nfn, sizeof(Fn), cmp);
    edges = calloc(1u << EDGE_BITS, sizeof(Edge));
    printf("tracing %d functions in pid %lu for %d s (cap %d hits each)\n", nfn, pid, seconds, cap);

    if (!DebugActiveProcess(pid)) { fprintf(stderr, "DebugActiveProcess failed: %lu\n", GetLastError()); return 1; }
    DebugSetProcessKillOnExit(FALSE);
    proc = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
    if (!proc) { fprintf(stderr, "OpenProcess failed: %lu\n", GetLastError()); return 1; }

    DWORD seq = 0, cur_phase = 31, start = GetTickCount();
    char stopname[600];
    snprintf(stopname, sizeof stopname, "%s.stop", prefix);
    int patched = 0, running = 1;
    DWORD total_hits = 0, skipped = 0;
    while (running) {
        DEBUG_EVENT ev;
        if (!WaitForDebugEvent(&ev, 100)) {
            if (GetTickCount() - start > (DWORD)seconds * 1000u || GetFileAttributesA(stopname) != INVALID_FILE_ATTRIBUTES) running = 0;
            continue;
        }
        DWORD cont = DBG_CONTINUE;
        switch (ev.dwDebugEventCode) {
        case EXIT_PROCESS_DEBUG_EVENT:
            running = 0; patched = 0;
            break;
        case EXCEPTION_DEBUG_EVENT: {
            DWORD code = ev.u.Exception.ExceptionRecord.ExceptionCode;
            DWORD addr = (DWORD)(ULONG_PTR)ev.u.Exception.ExceptionRecord.ExceptionAddress;
            if (code == EXCEPTION_BREAKPOINT) {
                if (!patched) {                       /* the attach breakpoint: plant ours */
                    for (int i = 0; i < nfn; i++) {
                        SIZE_T n;
                        if (ReadProcessMemory(proc, (LPVOID)fns[i].addr, &fns[i].orig, 1, &n) && n == 1 && fns[i].orig != 0xCC) {
                            put_byte(fns[i].addr, 0xCC);
                            fns[i].armed = 1;
                        }
                    }
                    patched = 1;
                    printf("breakpoints planted\n");
                    fflush(stdout);
                    break;
                }
                int idx = find_fn(addr);
                if (idx < 0 || !fns[idx].armed) break;   /* not ours */
                HANDLE th = OpenThread(THREAD_ALL_ACCESS, FALSE, ev.dwThreadId);
                CONTEXT ctx;
                ctx.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
                if (th && GetThreadContext(th, &ctx)) {
                    DWORD ret = 0; SIZE_T n;
                    ReadProcessMemory(proc, (LPVOID)ctx.Esp, &ret, 4, &n);
                    Fn *fn = &fns[idx];
                    if (fn->hits == 0) { fn->first_seq = ++seq; }
                    fn->hits++;
                    total_hits++;
                    fn->phases |= 1u << (cur_phase & 31);
                    int ci = containing_fn(ret);
                    DWORD caller = (ci >= 0 && ret - fns[ci].addr < 0x4000) ? fns[ci].addr : 0;
                    if (fn->hits == 1) fn->first_caller = caller;
                    add_edge(caller, fn->addr);
                    if (addr == phase_fn) {
                        DWORD ph = 0;
                        if (ReadProcessMemory(proc, (LPVOID)(ctx.Ecx + 4), &ph, 4, &n)) cur_phase = ph;
                    }
                    put_byte(fn->addr, fn->orig);
                    fn->armed = 0;
                    if (fn->hits >= (DWORD)cap) fn->disabled = 1;
                    ctx.Eip = fn->addr;
                    ctx.EFlags |= 0x100;               /* single step over the restored instruction, then re-arm */
                    SetThreadContext(th, &ctx);
                    for (int k = 0; k < 256; k++) if (pending[k].tid == 0 || pending[k].tid == ev.dwThreadId) { pending[k].tid = ev.dwThreadId; pending[k].fn = idx; break; }
                } else skipped++;
                if (th) CloseHandle(th);
            } else if (code == EXCEPTION_SINGLE_STEP) {
                for (int k = 0; k < 256; k++) {
                    if (pending[k].tid == ev.dwThreadId) {
                        Fn *fn = &fns[pending[k].fn];
                        if (!fn->disabled) { put_byte(fn->addr, 0xCC); fn->armed = 1; }
                        pending[k].tid = 0;
                        HANDLE th = OpenThread(THREAD_ALL_ACCESS, FALSE, ev.dwThreadId);
                        CONTEXT ctx;
                        ctx.ContextFlags = CONTEXT_CONTROL;
                        if (th && GetThreadContext(th, &ctx)) { ctx.EFlags &= ~0x100u; SetThreadContext(th, &ctx); }
                        if (th) CloseHandle(th);
                        break;
                    }
                }
            } else {
                cont = DBG_EXCEPTION_NOT_HANDLED;      /* the game's own exceptions */
            }
            break;
        }
        default:
            break;
        }
        ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, cont);
        if (GetTickCount() - start > (DWORD)seconds * 1000u) running = 0;
    }
    /* detach: put every original byte back first */
    if (patched) {
        for (int i = 0; i < nfn; i++) if (fns[i].armed) put_byte(fns[i].addr, fns[i].orig);
    }
    DebugActiveProcessStop(pid);

    char name[600];
    snprintf(name, sizeof name, "%s_funcs.tsv", prefix);
    FILE *o = fopen(name, "w");
    int seen = 0;
    for (int i = 0; i < nfn; i++) {
        if (!fns[i].hits) continue;
        seen++;
        fprintf(o, "%08lx\t%lu\t%lu\t%08lx\t%08lx\t%d\n", (unsigned long)fns[i].addr, (unsigned long)fns[i].hits, (unsigned long)fns[i].first_seq,
                (unsigned long)fns[i].phases, (unsigned long)fns[i].first_caller, fns[i].disabled);
    }
    fclose(o);
    snprintf(name, sizeof name, "%s_edges.tsv", prefix);
    o = fopen(name, "w");
    int ne = 0;
    for (unsigned i = 0; i < (1u << EDGE_BITS); i++) if (edges[i].count) { ne++; fprintf(o, "%08lx\t%08lx\t%lu\n", (unsigned long)edges[i].caller, (unsigned long)edges[i].callee, (unsigned long)edges[i].count); }
    fclose(o);
    printf("done: %d of %d functions hit, %lu breakpoint hits, %d distinct edges, %lu hits skipped\n", seen, nfn, (unsigned long)total_hits, ne, (unsigned long)skipped);
    return 0;
}
