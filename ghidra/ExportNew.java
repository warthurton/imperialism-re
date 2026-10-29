import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.io.File;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.util.HashSet;
import java.util.Set;

// Post-script: decompile only functions whose entry address is NOT in the old export.
// Arg 0 = output file, arg 1 = text file of already-exported entry addresses (8 hex digits per line).
public class ExportNew extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Set<String> old = new HashSet<>();
        for (String l : Files.readAllLines(new File(args[1]).toPath())) old.add(l.trim());
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int ok = 0, fail = 0;
        try (PrintWriter w = new PrintWriter(new File(args[0]), "UTF-8")) {
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (monitor.isCancelled()) break;
                if (old.contains(f.getEntryPoint().toString())) continue;
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
        println("ExportNew: " + ok + " new functions, " + fail + " failed");
    }
}
