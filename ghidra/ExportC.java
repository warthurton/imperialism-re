import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.io.File;
import java.io.PrintWriter;

public class ExportC extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File out = new File(args.length > 0 ? args[0] : "imperialism_decomp.c");
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int ok = 0, fail = 0;
        try (PrintWriter w = new PrintWriter(out, "UTF-8")) {
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (monitor.isCancelled()) break;
                DecompileResults r = ifc.decompileFunction(f, 60, monitor);
                if (r.decompileCompleted()) {
                    w.println("// " + f.getName() + " @ " + f.getEntryPoint());
                    w.println(r.getDecompiledFunction().getC());
                    ok++;
                } else {
                    w.println("// FAILED " + f.getName() + " @ " + f.getEntryPoint());
                    fail++;
                }
            }
        }
        println("Exported " + ok + " functions, " + fail + " failed -> " + out);
    }
}
