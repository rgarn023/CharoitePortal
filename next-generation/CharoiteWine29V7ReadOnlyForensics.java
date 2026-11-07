package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Strict read-only examination of the two PRESERVED Wine29 v7 log files.
 * Never creates/executes/cleans/retries Wine or creates any scratch or prefix.
 * Does not inspect registry contents, older generations, user files or rootfs.
 */
public final class CharoiteWine29V7ReadOnlyForensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-services-v7";
    private static final String PE_LOG = "v7-wine-direct-init.log";
    private static final String SERVER_LOG = "v7-foreground-wineserver.log";
    private static final String REVISION = "v1-v7-services-process-correlated-readonly";
    private static final long MAX_PE_LOG = 2L * 1024L * 1024L;
    private static final long MAX_SERVER_LOG = 2L * 1024L * 1024L;
    private static final int MAX_LINES = 60000;
    private static final int MAX_LINE = 16384;
    private static final int MAX_PROCESSES = 48;
    private static final Pattern PID = Pattern.compile("^([0-9a-fA-F]{4}):.*");
    private static final Pattern EXIT = Pattern.compile("exit_code[= ]+(-?[0-9]+)", Pattern.CASE_INSENSITIVE);

    private CharoiteWine29V7ReadOnlyForensics() {}

    private static File evidence(File root, String relative) throws Exception {
        File base = root.getCanonicalFile();
        File file = new File(base, relative);
        if (file.equals(base) || !file.getCanonicalFile().toPath().startsWith(base.toPath())
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Retained v7 evidence path is linked/outside v7 scratch");
        return file;
    }

    private static void metadata(File scratch, StringBuilder out, String relative) throws Exception {
        File f = evidence(scratch, relative);
        out.append("v7/").append(relative).append(": ");
        if (!f.exists()) out.append("absent\n");
        else if (f.isFile()) out.append("file, contents NOT READ\n");
        else if (f.isDirectory()) out.append("directory, NOT entered\n");
        else out.append("unexpected type, NOT entered\n");
    }

    private static void cLink(File scratch, StringBuilder out) {
        File f = new File(scratch, "prefix/dosdevices/c:");
        out.append("v7/prefix/dosdevices/c: ");
        try {
            StructStat stat = Os.lstat(f.getAbsolutePath());
            if (!OsConstants.S_ISLNK(stat.st_mode))
                out.append("unexpected non-symlink; NOT followed\n");
            else
                out.append("../drive_c".equals(Os.readlink(f.getAbsolutePath()))
                        ? "correct relative link, NOT followed\n"
                        : "unexpected link, NOT followed\n");
        } catch (Exception e) {
            out.append("missing or inaccessible, no write attempted\n");
        }
    }

    private static class ProcessRecord {
        boolean mapsWineboot, mapsServices, mapsNtdll, mapsKernel, mapsApisets;
        int serviceLookupLines, failures, exits;
        String lastExit = "not observed";
        String firstExit = "not observed";
    }

    private static String pid(String line) {
        Matcher m = PID.matcher(line);
        return m.matches() ? m.group(1).toLowerCase(Locale.US) : null;
    }

    private static String summarizeCode(String dec) {
        try {
            long code = Long.parseLong(dec);
            return String.format(Locale.US, "%s (0x%08X)", dec, (int)code);
        } catch (Exception e) {
            return "unparseable";
        }
    }

    private static void peAudit(File scratch, StringBuilder out) throws Exception {
        File log = evidence(scratch, PE_LOG);
        if (!log.isFile()) {
            out.append("v7 PE log absent; no automatic rerun attempted\n");
            return;
        }
        long length = log.length();
        if (length <= 0 || length > MAX_PE_LOG) {
            out.append("v7 PE log ").append(length)
                .append(" bytes OUTSIDE 2 MiB read-only bound; contents NOT READ\n");
            return;
        }
        LinkedHashMap<String,ProcessRecord> table = new LinkedHashMap<>();
        int lines=0, serviceMentions=0, serviceRequests=0, serviceMappings=0;
        int serviceBuiltinFailures=0, createRequests=0, bootInitRequests=0;
        int dllNotFound=0, fatalErrors=0, genericErrors=0, overlong=0;
        int exitEvents=0, nonzeroEvents=0, serverRelated=0;
        java.util.ArrayList<String> requests = new java.util.ArrayList<>();
        java.util.ArrayList<String> serviceClues = new java.util.ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (++lines > MAX_LINES)
                    throw new SecurityException("v7 PE log exceeds maximum line count");
                if (line.length() > MAX_LINE) { overlong++; continue; }
                String lower = line.toLowerCase(Locale.US);
                String id = pid(line);
                ProcessRecord p = id != null ? table.get(id) : null;
                if (p == null && id != null && table.size() < MAX_PROCESSES) {
                    p = new ProcessRecord();
                    table.put(id,p);
                }
                boolean service = lower.contains("services.exe");
                if (service) serviceMentions++;
                if (lower.contains("ntcreateuserprocess") && lower.contains(" image ")) {
                    createRequests++;
                    if (lower.contains("wineboot.exe") && lower.contains("--init"))
                        bootInitRequests++;
                    if (service) serviceRequests++;
                    if (requests.size() < 12) {
                        String exe = service ? "services.exe" :
                            lower.contains("wineboot.exe") ? "wineboot.exe" :
                            lower.contains(".exe") ? "other .exe" : "unknown image";
                        requests.add("PE line " + lines + ": caller 0x" +
                            (id == null ? "unknown" : id) + " requested " + exe);
                    }
                }
                if (service && lower.contains("get_load_order") && p != null)
                    p.serviceLookupLines++;
                if (lower.contains("mapping pe file") && p != null) {
                    if (lower.contains("wineboot.exe")) p.mapsWineboot = true;
                    if (service) { p.mapsServices = true; serviceMappings++; }
                    if (lower.contains("ntdll.dll")) p.mapsNtdll = true;
                    if (lower.contains("kernel32.dll")) p.mapsKernel = true;
                }
                if (lower.contains("load_apiset_dll loaded") && p != null)
                    p.mapsApisets = true;
                if (service && lower.contains("cannot find builtin library")) {
                    serviceBuiltinFailures++;
                    if (p != null) p.failures++;
                }
                if (lower.contains("c0000135") || lower.contains("status_dll_not_found"))
                    dllNotFound++;
                if (lower.contains("fatal_error") || lower.contains("err:module:"))
                    fatalErrors++;
                if (lower.contains("err:") || lower.contains("failed")) genericErrors++;
                if (lower.contains("wineserver")) serverRelated++;
                if (service && serviceClues.size() < 12) {
                    String kind = lower.contains("ntcreateuserprocess") ? "process-create" :
                         lower.contains("mapping pe file") ? "PE image mapped" :
                         lower.contains("cannot find builtin library") ? "builtin lookup FAILED" :
                         lower.contains("get_load_order") ? "load-order lookup" :
                         lower.contains("ntterminateprocess") ? "process exit" : "other services.exe reference";
                    serviceClues.add("PE line " + lines + " PID 0x" +
                         (id == null ? "unknown" : id) + ": " + kind);
                }
                if (lower.contains("ntterminateprocess") && lower.contains("exit_code")) {
                    exitEvents++;
                    Matcher code=EXIT.matcher(line);
                    if (code.find()) {
                        if (!"0".equals(code.group(1))) nonzeroEvents++;
                        if (p != null) {
                            p.exits++;
                            if ("not observed".equals(p.firstExit)) p.firstExit=code.group(1);
                            p.lastExit=code.group(1);
                        }
                    }
                }
            }
        }
        out.append("v7 PE log: ").append(length).append(" bytes / ")
           .append(lines).append(" lines, READ ONLY; oversized lines skipped=").append(overlong).append('\n');
        out.append("PE process create requests=").append(createRequests)
           .append("; internal Wineboot --init requests=").append(bootInitRequests)
           .append("; services.exe process-create requests=").append(serviceRequests).append('\n');
        out.append("PE services.exe mentions=").append(serviceMentions)
           .append("; services.exe mapped PE images=").append(serviceMappings)
           .append("; services builtin lookup failures=").append(serviceBuiltinFailures).append('\n');
        out.append("PE DLL_NOT_FOUND status mentions=").append(dllNotFound)
           .append("; fatal/module error markers=").append(fatalErrors)
           .append("; other err:/failed mentions=").append(genericErrors)
           .append("; wineserver textual references=").append(serverRelated).append('\n');
        out.append("PE process exit trace events=").append(exitEvents)
           .append("; nonzero exit EVENTS (not necessarily distinct PIDs)=").append(nonzeroEvents).append('\n');
        out.append("Process creation summary, bounded (identity from image field only):\n");
        for (String event : requests) out.append("  ").append(event).append('\n');
        out.append("services.exe chronology, up to 12 event TYPES (no raw paths):\n");
        for (String event : serviceClues) out.append("  ").append(event).append('\n');
        for (Map.Entry<String,ProcessRecord> entry:table.entrySet()) {
            ProcessRecord p = entry.getValue();
            if (p.exits == 0 && !p.mapsWineboot && !p.mapsServices && p.serviceLookupLines==0)
                continue;
            out.append("PE PID 0x").append(entry.getKey())
               .append(": wineboot_mapped=").append(p.mapsWineboot)
               .append(" services_mapped=").append(p.mapsServices)
               .append(" ntdll_mapped=").append(p.mapsNtdll)
               .append(" kernel32_mapped=").append(p.mapsKernel)
               .append(" apiset_loaded=").append(p.mapsApisets)
               .append(" services_lookups=").append(p.serviceLookupLines)
               .append(" service_builtin_failures=").append(p.failures)
               .append(" exit_events=").append(p.exits)
               .append(" first_exit=").append(summarizeCode(p.firstExit))
               .append(" last_exit=").append(summarizeCode(p.lastExit)).append('\n');
        }
        out.append("PE INTERPRETATION: services.exe absent from the trace is NOT proof it ran, ")
           .append("nor proof it failed; Wineboot exit 0 does NOT verify service initialization.\n");
    }

    private static void serverAudit(File scratch, StringBuilder out) throws Exception {
        File log = evidence(scratch, SERVER_LOG);
        if (!log.isFile()) {
            out.append("v7 server log absent, no process rerun attempted\n");
            return;
        }
        long length = log.length();
        if (length <= 0 || length > MAX_SERVER_LOG) {
            out.append("v7 server log ").append(length)
               .append(" bytes OUTSIDE 2 MiB read-only bound; contents NOT READ\n");
            return;
        }
        int lines=0, overlong=0, serverStart=0, serviceMentions=0, processCreates=0;
        int newProcessReplies=0, initialThreads=0, missing=0, err=0, statusDll=0, shutdown=0;
        java.util.ArrayList<String> timeline = new java.util.ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line=reader.readLine()) != null) {
                if (++lines > MAX_LINES)
                    throw new SecurityException("v7 server log exceeds maximum line count");
                if (line.length()>MAX_LINE) {overlong++; continue;}
                String lower=line.toLowerCase(Locale.US);
                if (lower.contains("wineserver: starting")) serverStart++;
                if (lower.contains("services.exe")) serviceMentions++;
                if (lower.contains("new_process(") && !lower.contains("new_process()"))
                    processCreates++;
                if (lower.contains("new_process() =")) newProcessReplies++;
                if (lower.contains("init_first_thread")) initialThreads++;
                if (lower.contains("no_such_file") || lower.contains("object_name_not_found"))
                    missing++;
                if (lower.contains("fatal") || lower.contains("err:")) err++;
                if (lower.contains("c0000135") || lower.contains("status_dll_not_found"))
                    statusDll++;
                if (lower.contains("shutdown") || lower.contains("server: exiting")) shutdown++;
                if (timeline.size()<12 && (lower.contains("services.exe") ||
                    lower.contains("new_process(") || lower.contains("new_process() =") ||
                    lower.contains("get_new_process_info() ="))) {
                    String type = lower.contains("services.exe") ? "services.exe reference" :
                        lower.contains("get_new_process_info") ? "new-process handshake result" :
                        lower.contains("new_process() =") ? "new-process reply" : "new-process request";
                    timeline.add("server line " + lines + " PID 0x" +
                        (pid(line)==null ? "unknown" : pid(line)) + ": " + type);
                }
            }
        }
        out.append("v7 server log: ").append(length).append(" bytes / ")
           .append(lines).append(" lines, READ ONLY; oversized lines skipped=").append(overlong).append('\n');
        out.append("Server-start=").append(serverStart)
           .append("; services.exe mentions=").append(serviceMentions)
           .append("; new-process requests=").append(processCreates)
           .append("; new-process replies=").append(newProcessReplies)
           .append("; first-thread mentions=").append(initialThreads).append('\n');
        out.append("Server missing-name statuses=").append(missing)
           .append("; fatal/err markers=").append(err)
           .append("; DLL_NOT_FOUND markers=").append(statusDll)
           .append("; shutdown textual mentions=").append(shutdown).append('\n');
        out.append("Server process chronology, up to 12 event TYPES (no raw paths):\n");
        for (String event : timeline) out.append("  ").append(event).append('\n');
        out.append("SERVER INTERPRETATION: process handshake text alone does NOT identify a services.exe child ")
           .append("or prove service control manager persistence.\n");
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — WINE29 V7 SERVICES.EXE PRESERVED POSTMORTEM\n");
        out.append("Audit revision: ").append(REVISION).append('\n');
        out.append("STRICT READ ONLY: NO Wine, Wineboot, services.exe, wineserver, processes, ")
           .append("scratch creation, writes, cleanup, or retries.\n");
        out.append("Only TWO fixed v7 log names and explicitly named v7 metadata entries; ")
           .append("NO v1–v6, stable Portal, game/save/user-prefix/rootfs access.\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT<26)
            return out.append("RESULT: BLOCKED — wrong package/Android version\n").toString();
        try {
            File base=context.getNoBackupFilesDir().getCanonicalFile();
            File scratch=evidence(base,SCRATCH);
            if (!scratch.isDirectory())
                return out.append("RESULT: BLOCKED — v7 scratch is absent; NOT created\n").toString();
            out.append("Previously used v7 scratch: present, untouched\n");
            cLink(scratch,out);
            for (String relative : new String[]{
                    "prefix/drive_c", "prefix/drive_c/windows",
                    "prefix/drive_c/windows/system32", "prefix/drive_c/users",
                    "prefix/drive_c/users/xuser/AppData", "prefix/drive_c/Program Files",
                    "prefix/system.reg", "prefix/user.reg", "prefix/userdef.reg",
                    "runtime/lib/wine/aarch64-windows/wineboot.exe",
                    "runtime/lib/wine/aarch64-windows/services.exe"}) {
                metadata(scratch,out,relative);
            }
            try {
                peAudit(scratch,out);
            } catch (SecurityException e) {
                out.append("PE AUDIT ONLY BLOCKED: ").append(e.getMessage())
                   .append("; preserved evidence unchanged.\n");
            }
            try {
                serverAudit(scratch,out);
            } catch (SecurityException e) {
                out.append("SERVER AUDIT ONLY BLOCKED: ").append(e.getMessage())
                   .append("; preserved evidence unchanged.\n");
            }
            out.append("RESULT: READ-ONLY V7 AUDIT FINISHED. services.exe execution, ")
               .append("complete prefix initialization, graphics and Windows runtime NOT yet verified.\n");
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — ").append(e.getClass().getSimpleName())
               .append("; reason: ")
               .append(e instanceof SecurityException ? e.getMessage() : "bounded read failure")
               .append("; no changes to preserved v7 evidence.\n");
        }
        return out.toString();
    }
}
