package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Read-only v3 postmortem. Never invokes Wine, wineserver, wineboot, or another
 * program; does not create, modify, clean up, or retry any scratch or prefix.
 * Reads only two known bounded logs and five named, hash-verified PE images
 * in the existing private Wine29 v3 scratch; never reads prefix contents.
 */
public final class CharoiteWine29V3AutoInitForensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-pe-dir-v3";
    private static final String INDEX = "charoite-next/wine29-sealed012/wine29-sealed012-index.json";
    private static final String PE = "runtime/lib/wine/aarch64-windows/";
    private static final String BOOT = "runtime/lib/wine/aarch64-windows/wineboot.exe";
    private static final int MAX_PE = 2 * 1024 * 1024;
    private static final int MAX_SERVER = 256 * 1024;
    private static final int MAX_HITS = 80;
    private CharoiteWine29V3AutoInitForensics() {}

    private static File direct(File root, String name) throws Exception {
        File base = root.getCanonicalFile();
        File file = new File(base, name);
        if (file.equals(base) || !file.getCanonicalFile().toPath().startsWith(base.toPath())
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Unsafe Wine29 v3 read-only evidence path");
        return file;
    }

    private static String scrub(String line, String scratch) {
        String lower = line.toLowerCase(Locale.US);
        // The Wine debug trace can contain full inherited environment strings.
        if (lower.contains("env=") || lower.contains("password")
                || lower.contains("token=") || lower.contains("secret")
                || lower.contains("credential"))
            return "[redacted sensitive log line]";
        line = line.replace(scratch, "[v3-private-scratch]");
        line = line.replace('\r', ' ').replace('\0', ' ');
        return line.length() > 760 ? line.substring(0, 760) + " [clipped]" : line;
    }

    private static boolean relevant(String line) {
        String x = line.toLowerCase(Locale.US);
        return x.contains("ntcreateuserprocess")
                || x.contains("run_wineboot")
                || x.contains("wineboot.exe")
                || x.contains("wineboot:main")
                || x.contains("cannot set the dir")
                || x.contains("usage: wineboot")
                || x.contains("mapping pe file")
                || x.contains("load_dll")
                || x.contains("kernel32.dll")
                || x.contains("kernelbase.dll")
                || x.contains("ws2_32.so")
                || x.contains("get_builtin_unix_funcs")
                || x.contains("c0000135")
                || x.contains("c0000034")
                || x.contains("c000003a")
                || x.contains("get_pe_file_info")
                || x.contains("error:")
                || x.contains("failed");
    }

    private static int readU16(byte[] data, int at) {
        if (at < 0 || at > data.length - 2)
            throw new SecurityException("Wine29 preserved PE header out of bound");
        return (data[at] & 255) | ((data[at + 1] & 255) << 8);
    }

    private static long readU32(byte[] data, int at) {
        return Integer.toUnsignedLong(readU16(data, at) | (readU16(data, at + 2) << 16));
    }

    /** Source-hash-verified named v3 copy only; at most 4096 header bytes.
     * Raw COFF machine does not by itself establish ARM64EC hybrid loadability.
     */
    private static void inspectPeHeader(File file, String label, StringBuilder out)
            throws Exception {
        if (!file.isFile() || file.length() < 128
                || file.length() > 32L * 1024L * 1024L)
            throw new SecurityException("Unsafe Wine29 v3 PE header size");
        byte[] head = new byte[(int)Math.min(4096, file.length())];
        try (RandomAccessFile reader = new RandomAccessFile(file, "r")) {
            reader.readFully(head);
        }
        long pePosition = readU32(head, 0x3c);
        if (readU16(head, 0) != 0x5a4d || pePosition < 64
                || pePosition > head.length - 26
                || readU32(head, (int)pePosition) != 0x4550L)
            throw new SecurityException("Invalid Wine29 preserved PE header");
        int pe = (int)pePosition;
        int rawMachine = readU16(head, pe + 4);
        int sections = readU16(head, pe + 6);
        int optionalSize = readU16(head, pe + 20);
        int magic = readU16(head, pe + 24);
        if (sections < 1 || sections > 96 || optionalSize < 112
                || magic != 0x20b)
            throw new SecurityException("Invalid Wine29 preserved PE32+ metadata");
        String machine = rawMachine == 0xaa64 ? "ARM64 (AA64)"
                : rawMachine == 0xa641 ? "ARM64EC (A641)"
                : "OTHER (0x" + Integer.toHexString(rawMachine) + ")";
        out.append("v3 PE header ").append(label)
           .append(": MZ/PE32+ PASS; raw COFF ")
           .append(machine).append("; sections ")
           .append(sections).append("; source hash already verified\n");
    }

    private static void inspect(StringBuilder out, File scratch, String filename,
                                int limit) throws Exception {
        File log = direct(scratch, filename);
        out.append("\n").append(filename).append(": ");
        if (!log.isFile()) {
            out.append("absent; NOT read and NOT created\n");
            return;
        }
        long length = log.length();
        if (length < 0 || length > limit)
            throw new SecurityException("v3 preserved diagnostic log exceeds read-only cap");
        ByteArrayOutputStream bytes = new ByteArrayOutputStream((int)length);
        try (FileInputStream input = new FileInputStream(log)) {
            byte[] block = new byte[16384];
            int n;
            while ((n = input.read(block)) != -1) {
                if (bytes.size() + n > limit)
                    throw new SecurityException("v3 log grew beyond read-only cap");
                bytes.write(block,0,n);
            }
        }
        String[] lines = new String(bytes.toByteArray(), StandardCharsets.UTF_8).split("\n");
        out.append(length).append(" bytes; ").append(lines.length)
           .append(" lines; READ-ONLY\n");
        int internalCreate = 0, failureNtStatus = 0, mappedBoot = 0;
        int mappedNtdll = 0, mappedKernel32 = 0, initCmdline = 0;
        int usage = 0, cannotSetWindows = 0, missingNativeSo = 0;
        int firstCreate = -1, firstFailure = -1, firstWindows = -1;
        int firstNative = -1, lastHelp = -1, lastMappedKernel32 = -1;
        List<String> hits = new ArrayList<>();
        String root = scratch.getCanonicalPath();
        for (int i=0;i<lines.length;i++) {
            String line=lines[i], x=line.toLowerCase(Locale.US);
            if (x.contains("ntcreateuserprocess")) {
                internalCreate++; if (firstCreate<0) firstCreate=i;
            }
            if (x.contains("run_wineboot failed to start wineboot")) {
                failureNtStatus++; if (firstFailure<0) firstFailure=i;
            }
            if (x.contains("wineboot.exe") && x.contains("--init")) initCmdline++;
            if (x.contains("mapping pe file") && x.contains("wineboot.exe")) mappedBoot++;
            if (x.contains("mapping pe file") && x.contains("ntdll.dll")) mappedNtdll++;
            if (x.contains("mapping pe file") && x.contains("kernel32.dll")) {
                mappedKernel32++; lastMappedKernel32=i;
            }
            if (x.contains("usage: wineboot")) { usage++; lastHelp=i; }
            if (x.contains("cannot set the dir") && x.contains("windows")) {
                cannotSetWindows++; if (firstWindows<0) firstWindows=i;
            }
            if (x.contains("get_builtin_unix_funcs") && x.contains(".so")) {
                missingNativeSo++; if (firstNative<0) firstNative=i;
            }
            if (relevant(line)) hits.add(scrub(line,root));
        }
        out.append("AUTO-INIT CHILD-CREATION EVIDENCE (do not confuse with Wineboot exit code)\n")
           .append("NtCreateUserProcess lines=").append(internalCreate)
           .append(", --init command lines=").append(initCmdline)
           .append(", run_wineboot creation failure markers=").append(failureNtStatus)
           .append("\nWineboot PE mappings=").append(mappedBoot)
           .append(", NTDLL PE mappings=").append(mappedNtdll)
           .append(", kernel32 PE mappings=").append(mappedKernel32)
           .append(", Usage: wineboot markers=").append(usage)
           .append(", C:\\windows chdir failures=").append(cannotSetWindows)
           .append(", native .so diagnostic warnings=").append(missingNativeSo)
           .append('\n');
        out.append("Wine 10 source interpretation: run_wineboot reports the NTSTATUS ")
           .append("returned by NtCreateUserProcess when it is nonzero. ")
           .append("The literal 'failed to start wineboot 1' is a process-CREATION ")
           .append("status (hex 0x1), NOT a confirmed Wineboot process exit code.\n");
        out.append("A passed Wineboot --help does NOT prove a completed --init, ")
           .append("drive_c, system registry or runnable Windows environment.\n");
        // Focus on actual source of the remaining failure, not only late DLL hits.
        for (int center : new int[]{firstCreate,firstFailure,firstWindows,firstNative,
                                      lastMappedKernel32,lastHelp}) {
            if (center<0) continue;
            out.append("Preserved v3 context around line ").append(center+1)
               .append(" (max 5 lines; env redacted):\n");
            for (int j=Math.max(0,center-2);j<Math.min(lines.length,center+3);j++)
                out.append("  ").append(j+1).append(": ")
                   .append(scrub(lines[j],root)).append('\n');
        }
        out.append("Relevant lines (first + last up to ").append(MAX_HITS).append("):\n");
        int front=Math.min(hits.size(),MAX_HITS/2);
        int back=Math.min(hits.size()-front,MAX_HITS-front);
        for(int i=0;i<front;i++)out.append(hits.get(i)).append('\n');
        if(front+back<hits.size())out.append("[... ")
            .append(hits.size()-front-back).append(" relevant lines omitted ...]\n");
        for(int i=hits.size()-back;i<hits.size();i++)out.append(hits.get(i)).append('\n');
    }

    /**
     * Compare only five known v3 scratch PE module copies with the original
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
            out.append("v3 copied ").append(which).append(": ");
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
            boolean verified = hex.toString().equals(record.getString("sha256"));
            out.append(verified
                ? "SOURCE SHA-256 PASS\n" : "SOURCE SHA-256 MISMATCH (not repaired)\n");
            // Header parsing only after original immutable source SHA matches.
            if (verified) inspectPeHeader(copy, label, out);
        }
        // The old arm64-windows source copy also remains in v3; it is never launched by forensics.
        File alias = direct(scratch, "runtime/lib/wine/arm64-windows/wineboot.exe");
        out.append("v3 secondary ARM64 Wineboot copy: ")
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
        out.append("CHAROITE NEXT — WINE29 V3 READ-ONLY AUTO-INIT CHILD-CREATION POSTMORTEM\n");
        out.append("No Wine/Wineboot/wineserver execution, scratch creation, cleanup, retries or file writes.\n");
        out.append("Only v3 bounded logs, named PE headers, and prefix FILE TYPES; NO prefix content or older scratch read.\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — unexpected package\n").toString();
        try {
            File root = context.getNoBackupFilesDir().getCanonicalFile();
            File scratch = direct(root, SCRATCH);
            if (!scratch.isDirectory()
                    || !scratch.getCanonicalFile().getParentFile().equals(root))
                return out.append("RESULT: BLOCKED — existing v3 scratch absent or unsafe\n").toString();
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
            out.append("Expected v3 WINEDLLPATH root: runtime/lib/wine; ARM64 candidate: ")
               .append(PE).append("kernel32.dll (v3 --help mapped kernel32; automatic Wineboot spawn still unproven)\n");
            out.append("Module integrity plus --help success does not establish a runnable ")
               .append("prefix; the automatic Wineboot NtCreateUserProcess status remains the blocker.\n");
            inspect(out, scratch, "v3-wine-pe-help.log", MAX_PE);
            inspect(out, scratch, "v3-foreground-wineserver.log", MAX_SERVER);
            out.append("RESULT: PASS — v3 read-only postmortem finished; --help PASSED, automatic prefix initialization NOT VERIFIED\n");
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — v3 forensic read: ")
               .append(e.getClass().getSimpleName()).append('\n');
        }
        out.append("NEVER rerun v3 or remove any diagnostic scratch; no new Wine test was authorized.\n");
        return out.toString();
    }
}
