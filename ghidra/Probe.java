import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.io.File;
import java.io.PrintWriter;

// Post-script: decompile one function with a long timeout and report why it fails.
// Arg 0 = entry address (hex), arg 1 = output file, arg 2 = timeout seconds (default 600).
public class Probe extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Address a = currentProgram.getAddressFactory().getAddress(args[0]);
        int timeout = args.length > 2 ? Integer.parseInt(args[2]) : 600;
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        println("Probe: function " + f + " body=" + (f == null ? -1 : f.getBody().getNumAddresses()) + " addrs");
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        long t0 = System.currentTimeMillis();
        DecompileResults r = ifc.decompileFunction(f, timeout, monitor);
        println("Probe: completed=" + r.decompileCompleted() + " timedOut=" + r.isTimedOut() + " cancelled=" + r.isCancelled()
            + " failed=" + r.failedToStart() + " ms=" + (System.currentTimeMillis() - t0));
        println("Probe: error=" + r.getErrorMessage());
        if (r.decompileCompleted()) {
            try (PrintWriter w = new PrintWriter(new File(args[1]), "UTF-8")) {
                w.println("// " + f.getName() + " @ " + f.getEntryPoint());
                w.println(r.getDecompiledFunction().getC());
            }
        }
    }
}
