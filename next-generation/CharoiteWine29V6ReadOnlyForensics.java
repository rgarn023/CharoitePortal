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
 * READ ONLY inspection of ONLY retained Wine29 v6 one-shot evidence.
 * No Wine/PE/wineserver execution, process creation, retries, writes, cleanup,
 * prefix re-initialization or reading of registry data. No other generations
 * and no user game/prefix/save/rootfs paths are opened.
 */
public final class CharoiteWine29V6ReadOnlyForensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-child-loader-v6";
    private static final String PE_LOG = "v6-wine-direct-init.log";
    private static final String SERVER_LOG = "v6-foreground-wineserver.log";
    private static final String AUDIT_REVISION = "v3-0034-correlated-pe-server-evidence";
    private static final long MAX_PE_LOG = 2L * 1024L * 1024L;
    private static final long MAX_SERVER_LOG = 512L * 1024L; // Explicit v3 bounded server evidence (v0.83 was 256 KiB).
    private static final int MAX_LINES = 120000;
    private static final int MAX_LINE = 16384;
    private static final int MAX_PROCESSES = 24;
    private static final Pattern PROCESS = Pattern.compile("^([0-9a-fA-F]{4}):.*");
    private static final Pattern EXIT = Pattern.compile("exit_code[= ]+(-?[0-9]+)", Pattern.CASE_INSENSITIVE);

    private CharoiteWine29V6ReadOnlyForensics() {}

    private static File evidence(File root, String relative) throws Exception {
        File parent = root.getCanonicalFile();
        File candidate = new File(parent, relative);
        if (candidate.equals(parent)
                || !candidate.getCanonicalFile().toPath().startsWith(parent.toPath())
                || !candidate.getCanonicalFile().equals(candidate.getAbsoluteFile()))
            throw new SecurityException("Preserved v6 path is linked or escapes scratch");
        return candidate;
    }

    private static String safeLine(String line, String path) {
        String lower = line.toLowerCase(Locale.US);
        if (lower.contains("env=") || lower.contains("password")
                || lower.contains("secret") || lower.contains("token=")
                || lower.contains("credential") || lower.contains("authorization"))
            return "[sensitive trace line redacted]";
        String s = line.replace(path, "[v6-private-scratch]")
                .replace('\r', ' ').replace('\0', ' ');
        return s.length() > 280 ? s.substring(0, 280) + " [clipped]" : s;
    }

    private static final class Child {
        boolean mapsBoot, mapsNtdll, mapsKernel, mapsApiSet;
        boolean exitObserved;
        String lastExit = "not observed";
        int exitEvents;
    }

    private static void auditPe(File scratch, StringBuilder out) throws Exception {
        File log = evidence(scratch, PE_LOG);
        if (!log.isFile()) {
            out.append("v6 retained PE log: MISSING (no Wine run attempted)\n");
            return;
        }
        long length = log.length();
        if (length <= 0 || length > MAX_PE_LOG)
            throw new SecurityException("Preserved v6 PE log exceeds read-only limit");
        out.append("v6 retained PE log: ").append(length).append(" bytes; read-only\n");
        LinkedHashMap<String,Child> processes = new LinkedHashMap<>();
        int lines=0, childRequests=0, loaderFailures=0, execErrno=0;
        int status135=0, bootstrapMarkers=0, failedMessages=0;
        int missingBuiltin=0, bootstrapMode=0, processExitEvents=0;
        int filesCreated=0, caseSearchWarnings=0;
        String firstRequest = null, firstFailure = null, firstExit = null;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (++lines > MAX_LINES || line.length() > MAX_LINE)
                    throw new SecurityException("Preserved v6 PE log exceeds bounded line limits");
                String lower = line.toLowerCase(Locale.US);
                Matcher match = PROCESS.matcher(line);
                String pid = match.matches() ? match.group(1).toLowerCase(Locale.US) : null;
                Child child = null;
                if (pid != null) {
                    child = processes.get(pid);
                    if (child == null && processes.size() < MAX_PROCESSES) {
                        child = new Child();
                        processes.put(pid, child);
                    }
                }
                if (lower.contains("ntcreateuserprocess") && lower.contains("wineboot.exe")
                        && lower.contains("--init")) {
                    childRequests++;
                    if (firstRequest == null) firstRequest = safeLine(line, scratch.getAbsolutePath());
                }
                if (lower.contains("mapping pe file") && child != null) {
                    if (lower.contains("wineboot.exe")) child.mapsBoot = true;
                    if (lower.contains("ntdll.dll")) child.mapsNtdll = true;
                    if (lower.contains("kernel32.dll")) child.mapsKernel = true;
                }
                if (lower.contains("load_apiset_dll loaded")
                        && lower.contains("apisetschema.dll") && child != null)
                    child.mapsApiSet = true;
                if (lower.contains("run_wineboot failed to start wineboot")) {
                    loaderFailures++;
                    if (firstFailure == null)
                        firstFailure = safeLine(line, scratch.getAbsolutePath());
                }
                if (lower.contains("charoite_wine29_v6_child_execv_failure")) {
                    execErrno++;
                    if (firstFailure == null)
                        firstFailure = safeLine(line, scratch.getAbsolutePath());
                }
                if (lower.contains("c0000135")) status135++;
                if (lower.contains("wineboot:main") || lower.contains("wineboot finished")
                        || lower.contains("wineboot: init")) bootstrapMarkers++;
                if (lower.contains("failed") || lower.contains("err:")) failedMessages++;
                if (lower.contains("wineboot.exe") && lower.contains("not found")) missingBuiltin++;
                if (lower.contains("winebootstrapmode")) bootstrapMode++;
                if (lower.contains("created") && lower.contains("file")) filesCreated++;
                if (lower.contains("disabling case insensitive search")) caseSearchWarnings++;
                if (lower.contains("ntterminateprocess") && lower.contains("exit_code")) {
                    processExitEvents++;
                    if (child != null) {
                        child.exitObserved = true;
                        child.exitEvents++;
                        Matcher exit = EXIT.matcher(line);
                        if (exit.find()) child.lastExit = exit.group(1);
                    }
                    if (firstExit == null) firstExit = safeLine(line, scratch.getAbsolutePath());
                }
            }
        }
        out.append("PE log analyzed lines: ").append(lines).append('\n');
        out.append("Internal --init process-create requests: ").append(childRequests).append('\n');
        out.append("run_wineboot child-create failures: ").append(loaderFailures).append('\n');
        out.append("V6 native child execv errno markers: ").append(execErrno).append('\n');
        out.append("c0000135 occurrences: ").append(status135).append('\n');
        out.append("Wineboot main/init/finished trace markers: ").append(bootstrapMarkers).append(" (diagnostic only)\n");
        out.append("All err:/failed text occurrences: ").append(failedMessages).append(" (not all fatal)\n");
        out.append("Early C:\\\\windows\\\\system32\\\\wineboot.exe not-found references: ")
                .append(missingBuiltin).append(" (builtin mapping can follow)\n");
        out.append("Case-insensitive filename search warnings: ").append(caseSearchWarnings).append('\n');
        out.append("Bootstrap-mode textual mentions: ").append(bootstrapMode).append('\n');
        out.append("NtTerminateProcess exit-code trace events: ").append(processExitEvents).append('\n');
        boolean childMapped=false, childExit=false, childExitZero=false;
        for (Map.Entry<String,Child> entry:processes.entrySet()) {
            Child p=entry.getValue();
            if (!p.mapsBoot) continue;
            childMapped |= p.mapsNtdll;
            childExit |= p.exitObserved;
            childExitZero |= p.exitObserved && "0".equals(p.lastExit);
            out.append("PE wineboot process 0x").append(entry.getKey())
               .append(": wineboot mapped=").append(p.mapsBoot)
               .append(" ntdll mapped=").append(p.mapsNtdll)
               .append(" kernel32 mapped=").append(p.mapsKernel)
               .append(" apiset loaded=").append(p.mapsApiSet)
               .append(" process exit trace=").append(p.exitObserved)
               .append(" last exit code=").append(p.lastExit).append('\n');
        }
        if (firstRequest != null) out.append("Initial --init request: ").append(firstRequest).append('\n');
        if (firstFailure != null) out.append("First bounded startup failure: ").append(firstFailure).append('\n');
        if (firstExit != null) out.append("First bounded process-exit event: ").append(firstExit).append('\n');
        out.append("INFERENCE: child PE+NTDLL mapping observed=").append(childMapped)
           .append("; child's exit observed=").append(childExit)
           .append("; at least one child exit=0=").append(childExitZero).append('\n');
        if (childMapped && loaderFailures==0 && execErrno==0) {
            out.append("RESULT: CHILD STARTUP CONFIRMED — no prior v5 child creation failure marker.\n");
        } else {
            out.append("RESULT: CHILD STARTUP INCOMPLETE/UNCLEAR — preserved data only.\n");
        }
        out.append("WARNING: exit=0 or mapping alone is NOT completed prefix setup or verified Windows runtime.\n");
    }


    /** Additional bounded pass over the SAME preserved PE log. It identifies
     * nonzero-exit helper processes without running anything or reading user
     * files. This is necessary because v6 wineboot 0024/002c both exited 0
     * while an independent helper 0034 exited with STATUS_DLL_NOT_FOUND. */
    private static void auditNonzeroProcesses(File scratch, StringBuilder out) throws Exception {
        File log = evidence(scratch, PE_LOG);
        if (!log.isFile()) return;
        long size=log.length();
        if (size<=0 || size>MAX_PE_LOG)
            throw new SecurityException("v6 PE log outside fixed 2 MiB bound");
        final class ProcessInfo {
            String firstExe="not identified";
            String firstError="not observed";
            String firstNonzero="not observed";
            int exitEvents=0;
        }
        LinkedHashMap<String,ProcessInfo> processes=new LinkedHashMap<>();
        int lines=0, totalNonzero=0;
        int processRequests=0, helperLines=0, statusClues=0;
        java.util.ArrayList<String> requestSamples=new java.util.ArrayList<>();
        java.util.ArrayList<String> helperSamples=new java.util.ArrayList<>();
        java.util.ArrayList<String> statusSamples=new java.util.ArrayList<>();
        try (BufferedReader reader=new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line=reader.readLine())!=null) {
                if (++lines>MAX_LINES || line.length()>MAX_LINE)
                    throw new SecurityException("v6 PE failure audit outside bounded lines");
                Matcher proc=PROCESS.matcher(line);
                if (!proc.matches()) continue;
                String pid=proc.group(1).toLowerCase(Locale.US);
                ProcessInfo p=processes.get(pid);
                if (p==null && processes.size()<MAX_PROCESSES) {
                    p=new ProcessInfo();
                    processes.put(pid,p);
                }
                if (p==null) continue;
                String lower=line.toLowerCase(Locale.US);
                // Chronological clues only: the trace PID is NOT a proved
                // parent/child relationship or executable identity.
                if (lower.contains("ntcreateuserprocess")
                        || lower.contains("create_process")
                        || lower.contains("start_process")) {
                    processRequests++;
                    if (requestSamples.size()<8)
                        requestSamples.add("PE line "+lines+": "+safeLine(line,scratch.getAbsolutePath()));
                }
                if ("0034".equals(pid)) {
                    helperLines++;
                    if (helperSamples.size()<8)
                        helperSamples.add("PE line "+lines+": "+safeLine(line,scratch.getAbsolutePath()));
                }
                if (lower.contains("c0000135") || lower.contains("status_dll_not_found")) {
                    statusClues++;
                    if (statusSamples.size()<4)
                        statusSamples.add("PE line "+lines+": "+safeLine(line,scratch.getAbsolutePath()));
                }
                if (lower.contains("mapping pe file") && lower.contains(".exe")
                        && "not identified".equals(p.firstExe)) {
                    int end=lower.indexOf(".exe");
                    String leading=line.substring(0,end+4);
                    int start=Math.max(leading.lastIndexOf('\\'), leading.lastIndexOf('/'))+1;
                    String candidate=leading.substring(start);
                    if (candidate.matches("(?i)[a-z0-9_.-]{1,64}\\.exe"))
                        p.firstExe=candidate;
                }
                if ("not observed".equals(p.firstError)
                        && (lower.contains("err:module:") || lower.contains("err:environ:")
                            || lower.contains("c0000135")
                            || (lower.contains("library") && lower.contains("not found"))))
                    p.firstError=safeLine(line, scratch.getAbsolutePath());
                if (lower.contains("ntterminateprocess") && lower.contains("exit_code")) {
                    Matcher code=EXIT.matcher(line);
                    if (code.find()) {
                        p.exitEvents++;
                        if (!"0".equals(code.group(1))
                                && "not observed".equals(p.firstNonzero)) {
                            p.firstNonzero=code.group(1);
                            totalNonzero++;
                        }
                    }
                }
            }
        }
        out.append("FAILURE-SCOPED READ-ONLY PASS: ")
           .append(lines).append(" PE lines re-read; no process executed.\n");
        out.append("Distinct process IDs with observed nonzero exit: ")
           .append(totalNonzero).append('\n');
        for (Map.Entry<String,ProcessInfo> e:processes.entrySet()) {
            ProcessInfo p=e.getValue();
            if ("not observed".equals(p.firstNonzero)) continue;
            String hex="unavailable";
            try {
                hex=String.format(Locale.US,"0x%08X",
                        (int)Long.parseLong(p.firstNonzero));
            } catch (NumberFormatException ignored) {}
            out.append("Nonzero exit process 0x").append(e.getKey())
               .append(": executable=").append(p.firstExe)
               .append("; first exit=").append(p.firstNonzero)
               .append(" / ").append(hex)
               .append("; exit events=").append(p.exitEvents).append('\n');
            out.append("  Earliest module/load error: ").append(p.firstError).append('\n');
            if ("0xC0000135".equals(hex))
                out.append("  STATUS_DLL_NOT_FOUND: missing dependency identity ")
                   .append("NOT proven until the source of this failure is identified.\n");
        }
        out.append("Two wineboot exit-0 processes do not exclude a failed helper ")
           .append("or prove complete Windows prefix initialization.\n");
        out.append("PE chronological process-create clues: ").append(processRequests)
           .append("; captured at most 8. These are NOT proof of PID 0034 identity.\n");
        for (String event:requestSamples) out.append("  ").append(event).append('\n');
        out.append("PE process 0034 trace lines: ").append(helperLines)
           .append("; captured at most 8, bounded/redacted.\n");
        for (String event:helperSamples) out.append("  ").append(event).append('\n');
        out.append("PE DLL-not-found status text clues: ").append(statusClues)
           .append("; captured at most 4.\n");
        for (String event:statusSamples) out.append("  ").append(event).append('\n');
    }

    private static void auditServer(File scratch, StringBuilder out) throws Exception {
        File log = evidence(scratch, SERVER_LOG);
        if (!log.isFile()) {
            out.append("v6 retained foreground server log: MISSING\n");
            return;
        }
        long size = log.length();
        if (size <= 0 || size > MAX_SERVER_LOG) {
            out.append("v6 retained wineserver log ").append(size)
               .append(" bytes exceeds explicit read-only 512 KiB cap or is empty; ")
               .append("server contents NOT READ; PE audit preserved.\n");
            return;
        }
        int lines=0, startup=0, clientThreads=0, noSuchFile=0, errors=0, oversizedLines=0;
        int helperMentions=0, dllStatusMentions=0, processClueLines=0;
        java.util.ArrayList<String> boundedHints=new java.util.ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String s;
            while ((s=reader.readLine())!=null) {
                if (++lines > MAX_LINES)
                    throw new SecurityException("Preserved v6 server log exceeds bounded line-count limit");
                // Some Wine protocol lines exceed 16 KiB. Safely skip their
                // contents, keeping the original whole-file 256 KiB cap.
                if (s.length() > MAX_LINE) {oversizedLines++;continue;}
                String x=s.toLowerCase(Locale.US);
                if (x.contains("wineserver: starting")) startup++;
                if (x.contains("init_first_thread")) clientThreads++;
                if (x.contains("no_such_file")) noSuchFile++;
                if (x.contains("fatal") || x.contains("err:")) errors++;
                boolean mentionsHelper=x.contains("0034");
                boolean dllNotFound=x.contains("c0000135")
                        || x.contains("status_dll_not_found");
                boolean processClue=x.contains("get_new_process_info")
                        || x.contains("create_process") || x.contains("new_process")
                        || x.contains("wineboot.exe");
                if (mentionsHelper) helperMentions++;
                if (dllNotFound) dllStatusMentions++;
                if (processClue) processClueLines++;
                if ((mentionsHelper || dllNotFound || processClue)
                        && boundedHints.size()<16)
                    boundedHints.add("server line "+lines+": "
                            +safeLine(s,scratch.getAbsolutePath()));
            }
        }
        out.append("v6 server log: ").append(size).append(" bytes; ").append(lines).append(" lines; READ ONLY\n")
           .append("Server-start markers: ").append(startup)
           .append("; first-thread markers: ").append(clientThreads)
           .append("; NO_SUCH_FILE statuses: ").append(noSuchFile)
           .append("; fatal/err markers: ").append(errors)
           .append("; overlong lines skipped: ").append(oversizedLines).append('\n');
        out.append("Server 0034 text mentions: ").append(helperMentions)
           .append("; DLL-not-found text mentions: ").append(dllStatusMentions)
           .append("; process-start text clues: ").append(processClueLines).append('\n');
        out.append("At most 16 bounded server clue lines (chronological, NOT verified PID linkage):\n");
        for (String clue:boundedHints) out.append("  ").append(clue).append('\n');
        out.append("Server termination after direct -i is not by itself proof of failure.\n");
    }

    private static void pathStatus(File scratch, StringBuilder out, String name) throws Exception {
        File entry = evidence(scratch, name);
        out.append("v6/").append(name).append(": ");
        if (!entry.exists()) out.append("absent\n");
        else if (entry.isDirectory()) out.append("directory (not entered)\n");
        else if (entry.isFile()) out.append("file (contents not read)\n");
        else out.append("unexpected type (not entered)\n");
    }

    private static void mapping(File scratch, StringBuilder out) throws Exception {
        File link = new File(scratch,"prefix/dosdevices/c:");
        out.append("v6/prefix/dosdevices/c: ");
        try {
            StructStat st=Os.lstat(link.getAbsolutePath());
            if (!OsConstants.S_ISLNK(st.st_mode))
                out.append("unexpected non-symlink; NOT followed\n");
            else {
                String raw=Os.readlink(link.getAbsolutePath());
                out.append("../drive_c".equals(raw) ? "correct relative link (not followed)\n"
                                                       : "unexpected link target (not followed)\n");
            }
        } catch (android.system.ErrnoException e) {
            out.append("missing/unreadable; NOT created\n");
        }
    }

    public static String run(Context context) {
        StringBuilder out=new StringBuilder();
        out.append("CHAROITE NEXT — WINE29 V6 PRESERVED CHILD-STARTUP POSTMORTEM\n");
        out.append("Audit revision: ").append(AUDIT_REVISION).append('\n');
        out.append("STRICT READ ONLY; no Wine, Wineboot, wineserver, process creation, scratch creation, writes, cleanup or retries.\n");
        out.append("Only TWO named v6 logs and named v6 metadata paths; other generations, stable Portal, games, saves, user prefixes/rootfs NOT ACCESSED.\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return out.append("RESULT: BLOCKED — wrong package/device\n").toString();
        try {
            File privateBase = context.getNoBackupFilesDir().getCanonicalFile();
            File scratch = evidence(privateBase, SCRATCH);
            if (!scratch.isDirectory())
                return out.append("RESULT: BLOCKED — prior v6 scratch absent, NOT created\n").toString();
            out.append("Previously used v6 scratch: present (not recreated)\n");
            mapping(scratch,out);
            for (String name : new String[]{
                    "prefix/drive_c","prefix/drive_c/windows",
                    "prefix/drive_c/windows/system32","prefix/drive_c/users",
                    "prefix/drive_c/users/xuser/AppData","prefix/drive_c/Program Files",
                    "prefix/system.reg","prefix/user.reg","prefix/userdef.reg",
                    "runtime/lib/wine/aarch64-windows/wineboot.exe"}) {
                pathStatus(scratch,out,name);
            }
            auditPe(scratch,out);
            auditNonzeroProcesses(scratch,out);
            out.append("Server-log audit: read-only, explicit v3 512 KiB whole-file cap; ")
               .append("oversized individual lines safely skipped.\n");
            try {
                auditServer(scratch,out);
            } catch (SecurityException e) {
                out.append("SERVER AUDIT ONLY BLOCKED: ").append(e.getMessage())
                   .append("; preceding PE findings remain valid.\n");
            }
            out.append("RESULT: READ-ONLY POSTMORTEM FINISHED; successful wineboot ")
               .append("exit is not proof that all helpers or prefix initialization succeeded.\n");
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — ").append(e.getClass().getSimpleName())
               .append("; reason: ")
               .append(e instanceof SecurityException ? e.getMessage() : "bounded read failure")
               .append("; preserved v6 evidence unchanged.\n");
        }
        return out.toString();
    }
}
