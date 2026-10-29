import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.io.File;
import java.nio.file.Files;

// Pre-script: create functions at code entry points that auto-analysis never found
// (vtable slots and class factories). Arg 0 = text file, one hex address per line.
public class CreateEntries extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        int made = 0, had = 0, failed = 0;
        for (String line : Files.readAllLines(new File(args[0]).toPath())) {
            line = line.trim();
            if (line.isEmpty()) continue;
            Address a = toAddr("0x" + line);
            if (getFunctionAt(a) != null) { had++; continue; }
            if (getInstructionAt(a) == null) disassemble(a);
            Function f = createFunction(a, null);
            if (f != null) made++; else failed++;
        }
        println("CreateEntries: created " + made + ", already existed " + had + ", failed " + failed);
    }
}
