package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Read-only v9 postmortem. Never invokes Wine, wineserver, wineboot, or another
 * program; does not create, modify, clean up, or retry any scratch or prefix.
 * Reads only two known bounded log files in the existing private v9 directory.
 */
public final class CharoiteWine28V9Forensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine28-pe-help-v9-builtin-boot";
    private static final int MAX_PE = 2 * 1024 * 1024;
    private static final int MAX_SERVER = 256 * 1024;
    private static final int MAX_HITS = 110;
    private CharoiteWine28V9Forensics() {}

    private static File direct(File root, String name) throws Exception {
        File base = root.getCanonicalFile();
        File file = new File(base, name);
        if (file.equals(base) || !file.getCanonicalFile().toPath().startsWith(base.toPath())
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Unsafe v9 read-only evidence path");
        return file;
    }

    private static String scrub(String line, String scratch) {
        // Never disclose the massive new_process env= field or full Android app paths.
        int env = line.indexOf("env=L\"");
        if (env >= 0) line = line.substring(0, env) + "env=[redacted]";
        line = line.replace(scratch, "[v9-scratch]");
        line = line.replace('\r', ' ').replace('\0', ' ');
        return line.length() > 760 ? line.substring(0, 760) + " [clipped]" : line;
    }

    private static boolean relevant(String line) {
        String s = line.toLowerCase(Locale.US);
        return s.contains("run_wineboot")
                || s.contains("wineboot.exe")
                || s.contains("kernel32.dll")
                || s.contains("kernelbase.dll")
                || s.contains("apisetschema.dll")
                || s.contains("init_first_thread")
                || s.contains("new_process(")
                || s.contains("new_process()")
                || s.contains("get_new_process_info")
                || s.contains("init_process_done")
                || s.contains("process_exiting")
                || s.contains("status=c0000135")
                || s.contains("status=c000000f")
                || s.contains("error:") || s.contains("failed")
                || s.contains(" = no_such_file")
                || s.contains(" = not_implemented");
    }

    private static void inspect(StringBuilder out, File scratch, String filename,
                                int limit) throws Exception {
        File log = direct(scratch, filename);
        out.append("\n").append(filename).append(": ");
        if (!log.isFile()) {
            out.append("absent (no mutation)\n");
            return;
        }
        long length = log.length();
        out.append(length).append(" bytes; ");
        if (length > limit) {
            out.append("exceeds read-only cap ").append(limit).append("; NOT READ\n");
            return;
        }
        ByteArrayOutputStream bytes = new ByteArrayOutputStream((int)length);
        try (FileInputStream input = new FileInputStream(log)) {
            byte[] block = new byte[16384];
            int n;
            while ((n = input.read(block)) != -1) {
                if (bytes.size() + n > limit) throw new SecurityException("v9 log grew past cap");
                bytes.write(block, 0, n);
            }
        }
        String[] lines = new String(bytes.toByteArray(), StandardCharsets.UTF_8).split("\n");
        List<String> hits = new ArrayList<>();
        int newProcess = 0, boot = 0, kernel = 0, apiset = 0;
        int noFile = 0, failed = 0;
        String rootPath = scratch.getCanonicalPath();
        for (String line : lines) {
            String s = line.toLowerCase(Locale.US);
            if (s.contains("new_process(") || s.contains("new_process()")) newProcess++;
            if (s.contains("wineboot.exe") || s.contains("run_wineboot")) boot++;
            if (s.contains("kernel32.dll") || s.contains("kernelbase.dll")) kernel++;
            if (s.contains("apisetschema.dll")) apiset++;
            if (s.contains("no_such_file")) noFile++;
            if (s.contains("failed") || s.contains("c0000135")) failed++;
            if (relevant(line)) hits.add(scrub(line, rootPath));
        }
        out.append("READ-ONLY; total lines ").append(lines.length)
           .append("; matching lines ").append(hits.size()).append('\n');
        out.append("Counts: new_process=").append(newProcess)
           .append(", wineboot=").append(boot)
           .append(", kernel32/kernelbase=").append(kernel)
           .append(", apisetschema=").append(apiset)
           .append(", NO_SUCH_FILE=").append(noFile)
           .append(", failed/c0000135=").append(failed).append('\n');
        out.append("Relevant trace (up to ").append(MAX_HITS)
           .append(" lines, first and last; env redacted):\n");
        int front = Math.min(hits.size(), MAX_HITS / 2);
        int back = Math.min(hits.size() - front, MAX_HITS - front);
        for (int i = 0; i < front; i++) out.append(hits.get(i)).append('\n');
        if (front + back < hits.size()) out.append("[... ")
                .append(hits.size() - front - back).append(" matching lines omitted ...]\n");
        for (int i = hits.size() - back; i < hits.size(); i++)
            out.append(hits.get(i)).append('\n');
    }

    private static void status(StringBuilder out, File scratch, String name)
            throws Exception {
        File entry = direct(scratch, name);
        out.append(name).append(": ");
        if (!entry.exists()) out.append("absent");
        else if (entry.isFile()) out.append("file (not read)");
        else if (entry.isDirectory()) out.append("directory (not entered)");
        else out.append("other");
        out.append('\n');
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — WINE28 V9 READ-ONLY BOOTSTRAP POSTMORTEM\n");
        out.append("No Wine/Wineboot/wineserver execution, scratch creation, cleanup, retries or file writes.\n");
        out.append("Only two existing v9 trace logs; never read user prefixes/games/saves/rootfs or prior scratch.\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — unexpected package\n").toString();
        try {
            File root = context.getNoBackupFilesDir().getCanonicalFile();
            File scratch = direct(root, SCRATCH);
            if (!scratch.isDirectory()
                    || !scratch.getCanonicalFile().getParentFile().equals(root))
                return out.append("RESULT: BLOCKED — existing v9 scratch absent or unsafe\n").toString();
            status(out, scratch, "prefix");
            status(out, scratch, "prefix/system.reg");
            status(out, scratch, "prefix/user.reg");
            status(out, scratch, "prefix/drive_c");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/wineboot.exe");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/kernel32.dll");
            inspect(out, scratch, "v9-wine-pe-help.log", MAX_PE);
            inspect(out, scratch, "v9-foreground-wineserver.log", MAX_SERVER);
            out.append("RESULT: PASS — existing v9 evidence inspected READ-ONLY; Wineboot remains unproven\n");
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — v9 forensic read: ")
               .append(e.getClass().getSimpleName()).append('\n');
        }
        out.append("NEVER rerun v9 or remove any diagnostic scratch; no new Wine test was authorized.\n");
        return out.toString();
    }
}
