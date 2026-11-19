import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Runs the SCM startup sequence after the caller verifies a fresh experimental prefix. */
final class CharoiteWine29RpcSsStartup {
    private static final long MAX_OUTPUT_BYTES = 256 * 1024;
    private static final Pattern SERVICE =
            Pattern.compile("(?im)^\\h*SERVICE_NAME\\h*:\\h*RpcSs\\h*$");
    private static final Pattern STATE =
            Pattern.compile("(?im)^\\h*STATE\\h*:\\h*(\\d+)\\h+([A-Z_]+)\\h*$");

    interface ScCommand {
        ProcessBuilder prepare(String operation);
    }

    enum Result { RUNNING, START_FAILED, QUERY_FAILED, NOT_RUNNING }

    private CharoiteWine29RpcSsStartup() {}

    static Result run(ScCommand command, File scratch) throws IOException, InterruptedException {
        if (execute(command.prepare("start"), scratch, "rpcss-start.log") == null) {
            return Result.START_FAILED;
        }
        for (int attempt = 0; attempt < 5; attempt++) {
            String output = execute(command.prepare("query"), scratch, "rpcss-query-" + attempt + ".log");
            if (output == null) return Result.QUERY_FAILED;
            if (reportsRunning(output)) return Result.RUNNING;
            if (attempt < 4) Thread.sleep(400);
        }
        return Result.NOT_RUNNING;
    }

    static boolean reportsRunning(String output) {
        Matcher service = SERVICE.matcher(output);
        if (!service.find()) return false;
        int serviceEnd = service.end();
        if (service.find()) return false;
        Matcher state = STATE.matcher(output);
        if (!state.find() || state.start() < serviceEnd) return false;
        boolean running = "4".equals(state.group(1)) && "RUNNING".equalsIgnoreCase(state.group(2));
        return running && !state.find();
    }

    private static String execute(ProcessBuilder command, File scratch, String name)
            throws IOException, InterruptedException {
        File log = new File(scratch, name);
        Files.createFile(log.toPath());
        command.directory(scratch).redirectErrorStream(true).redirectOutput(log);
        Process process = command.start();
        try {
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
            while (!process.waitFor(100, TimeUnit.MILLISECONDS)) {
                if (log.length() > MAX_OUTPUT_BYTES || System.nanoTime() >= deadline) return null;
            }
            if (process.exitValue() != 0 || log.length() > MAX_OUTPUT_BYTES) return null;
            return new String(Files.readAllBytes(log.toPath()), StandardCharsets.UTF_8);
        } finally {
            if (process.isAlive()) {
                process.destroyForcibly();
                process.waitFor(2, TimeUnit.SECONDS);
            }
        }
    }
}
