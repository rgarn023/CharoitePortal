package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Read-only v1 postmortem. Never invokes Wine, wineserver, wineboot, or another
 * program; does not create, modify, clean up, or retry any scratch or prefix.
 * Reads only two known bounded logs and five named, hash-verified PE images
 * in the existing private Wine29 v1 scratch; never reads prefix contents.
 */
public final class CharoiteWine29V1Forensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-pe-help-v1";
    private static final String INDEX = "charoite-next/wine29-sealed012/wine29-sealed012-index.json";
    private static final String PE = "runtime/lib/wine/aarch64-windows/";
    private static final String BOOT = "runtime/lib/wine/arm64-windows/wineboot.exe";
    private static final int MAX_PE = 2 * 1024 * 1024;
    private static final int MAX_SERVER = 256 * 1024;
    private static final int MAX_HITS = 110;
    private CharoiteWine29V1Forensics() {}

    private static File direct(File root, String name) throws Exception {
        File base = root.getCanonicalFile();
        File file = new File(base, name);
        if (file.equals(base) || !file.getCanonicalFile().toPath().startsWith(base.toPath())
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Unsafe Wine29 v1 read-only evidence path");
        return file;
    }

    private static String scrub(String line, String scratch) {
        // Never disclose the massive new_process env= field or full Android app paths.
        int env = line.indexOf("env=L\"");
        if (env >= 0) line = line.substring(0, env) + "env=[redacted]";
        line = line.replace(scratch, "[v1-scratch]");
        line = line.replace('\r', ' ').replace('\0', ' ');
        return line.length() > 760 ? line.substring(0, 760) + " [clipped]" : line;
    }

    private static boolean relevant(String line) {
        String s = line.toLowerCase(Locale.US);
        return s.contains("run_wineboot")
                || s.contains("wineboot.exe")
                || s.contains("get_load_order")
                || s.contains("find_dll_file")
                || s.contains("load_dll")
                || s.contains("import_dll")
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
                if (bytes.size() + n > limit) throw new SecurityException("v1 log grew past cap");
                bytes.write(block, 0, n);
            }
        }
        String[] lines = new String(bytes.toByteArray(), StandardCharsets.UTF_8).split("\n");
        List<String> hits = new ArrayList<>();
        int newProcess = 0, boot = 0, kernel = 0, apiset = 0;
        int mappedNtdll = 0, mappedBoot = 0, loadedApi = 0;
        int noFile = 0, failed = 0;
        String rootPath = scratch.getCanonicalPath();
        for (String line : lines) {
            String s = line.toLowerCase(Locale.US);
            if (s.contains("new_process(") || s.contains("new_process()")) newProcess++;
            if (s.contains("wineboot.exe") || s.contains("run_wineboot")) boot++;
            if (s.contains("kernel32.dll") || s.contains("kernelbase.dll")) kernel++;
            if (s.contains("apisetschema.dll")) apiset++;
            if (s.contains("mapping pe file") && s.contains("ntdll.dll")) mappedNtdll++;
            if (s.contains("mapping pe file") && s.contains("wineboot.exe")) mappedBoot++;
            if (s.contains("load_apiset_dll loaded")) loadedApi++;
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
           .append(", mappedWineboot=").append(mappedBoot)
           .append(", mappedNtdll=").append(mappedNtdll)
           .append(", loadedApi=").append(loadedApi)
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

    /**
     * Compare only five known v1 scratch PE module copies with the original
     * immutable APK sealed index. Never touches older staged slots or prefixes.
     * A missing or mismatched file is diagnostic evidence, never auto-repaired.
     */
    private static void verifySelectedPe(Context context, File scratch, StringBuilder out)
            throws Exception {
        ByteArrayOutputStream raw = new ByteArrayOutputStream();
        try (java.io.InputStream input = context.getAssets().open(INDEX)) {
            byte[] chunk = new byte[4096]; int n;
            while ((n = input.read(chunk)) != -1) {
                if (raw.size() + n > 65536)
                    throw new SecurityException("Oversized Wine29 APK sealed index");
                raw.write(chunk, 0, n);
            }
        }
        JSONObject index = new JSONObject(raw.toString("UTF-8"));
        if (index.getInt("schema_version") != 1 ||
            index.getInt("module_count") != 111 ||
            !"com.charoitx".equals(index.getString("package")) ||
            !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(
                index.getString("wine_source_commit")) ||
            !"wine10-arm64ec-dependencies.0.12-sealed-data-candidate".equals(
                index.getString("bundle_version")))
            throw new SecurityException("Unexpected Wine29 sealed provenance in APK");
        JSONArray all = index.getJSONArray("module_files");
        String[] wanted = {
            "pe/arm64ec/kernel32.dll", "pe/arm64ec/kernelbase.dll",
            "pe/arm64ec/ntdll.dll", "pe/arm64ec/apisetschema.dll",
            "pe/arm64/wineboot.exe"
        };
        for (String which : wanted) {
            JSONObject record = null;
            for (int i = 0; i < all.length(); i++) {
                JSONObject entry = all.getJSONObject(i);
                if (which.equals(entry.getString("path"))) {
                    if (record != null) throw new SecurityException("Duplicate APK PE record");
                    record = entry;
                }
            }
            if (record == null) throw new SecurityException("Missing APK sealed PE record: " + which);
            String label = which.substring(which.lastIndexOf('/') + 1);
            File copy = direct(scratch, which.equals("pe/arm64/wineboot.exe")
                ? BOOT : PE + label);
            out.append("v1 copied ").append(which).append(": ");
            long size = record.getLong("size");
            if (!copy.isFile()) { out.append("ABSENT (not repaired)\n"); continue; }
            if (size <= 0 || size > 32L * 1024L * 1024L || copy.length() != size) {
                out.append("SIZE MISMATCH (not repaired)\n"); continue;
            }
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            try (FileInputStream input = new FileInputStream(copy)) {
                byte[] chunk = new byte[16384]; int n;
                while ((n = input.read(chunk)) != -1) sha.update(chunk, 0, n);
            }
            byte[] value = sha.digest();
            StringBuilder hex = new StringBuilder();
            for (byte b : value) hex.append(String.format(Locale.US, "%02x", b & 255));
            out.append(hex.toString().equals(record.getString("sha256"))
                ? "SOURCE SHA-256 PASS\n" : "SOURCE SHA-256 MISMATCH (not repaired)\n");
        }
        // A second source-matched builtin wineboot alias is copied in v1.
        File alias = direct(scratch, PE + "wineboot.exe");
        out.append("v1 builtin Wineboot alias: ")
           .append(alias.isFile() ? "file present (not executed)\n" : "absent\n");
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
        out.append("CHAROITE NEXT — WINE29 V1 READ-ONLY KERNEL32 BOOTSTRAP POSTMORTEM\n");
        out.append("No Wine/Wineboot/wineserver execution, scratch creation, cleanup, retries or file writes.\n");
        out.append("Only preserved v1 logs and five named PE copies; NO existing prefixes, games, saves, or older scratch read.\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — unexpected package\n").toString();
        try {
            File root = context.getNoBackupFilesDir().getCanonicalFile();
            File scratch = direct(root, SCRATCH);
            if (!scratch.isDirectory()
                    || !scratch.getCanonicalFile().getParentFile().equals(root))
                return out.append("RESULT: BLOCKED — existing v1 scratch absent or unsafe\n").toString();
            status(out, scratch, "prefix");
            status(out, scratch, "prefix/system.reg");
            status(out, scratch, "prefix/user.reg");
            status(out, scratch, "prefix/drive_c");
            status(out, scratch, "prefix/dosdevices");
            status(out, scratch, "prefix/.wineserver");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/wineboot.exe");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/kernel32.dll");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/kernelbase.dll");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/apisetschema.dll");
            status(out, scratch, "runtime/lib/wine/aarch64-windows/ntdll.dll");
            status(out, scratch, "runtime/lib/wine/arm64-windows/wineboot.exe");
            verifySelectedPe(context, scratch, out);
            inspect(out, scratch, "v1-wine-pe-help.log", MAX_PE);
            inspect(out, scratch, "v1-foreground-wineserver.log", MAX_SERVER);
            out.append("RESULT: PASS — v1 read-only forensic inspection completed; Wine29 PE-help remains FAILED at kernel32 c0000135\n");
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — v1 forensic read: ")
               .append(e.getClass().getSimpleName()).append('\n');
        }
        out.append("NEVER rerun v1 or remove any diagnostic scratch; no new Wine test was authorized.\n");
        return out.toString();
    }
}
