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
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Read-only preserved V15 evidence audit. Only three fixed V15 logs and named V15
 * metadata are examined. No processes, cleanup, writes, retries or other
 * generations. Registry contents are never opened; raw logs stay on phone.
 */
public final class CharoiteWine29V15ReadOnlyForensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-entry-v15";
    private static final String PE_LOG = "v15-wine-direct-init.log";
    private static final String ENTRY_LOG = "v15-sc-entry.log";
    private static final long MAX_SC_LOG = 8L * 1024L * 1024L;
    private static final String SERVER_LOG = "v15-foreground-wineserver.log";
    private static final long MAX_PE_LOG = 8L * 1024L * 1024L;
    private static final long MAX_SERVER_LOG = 8L * 1024L * 1024L;
    private static final int MAX_LINES = 100000;
    private static final int MAX_LINE = 16384;
    private static final int MAX_PROCESSES = 48;
    private static final int MAX_REPORT_CHARS = 9000;
    private static final Pattern PID = Pattern.compile("^([0-9a-fA-F]{4}):.*");
    private static final Pattern EXIT =
        Pattern.compile("exit_code[= ]+(-?[0-9]+)", Pattern.CASE_INSENSITIVE);
    private static final Pattern MODULE =
        Pattern.compile("(?i)([a-z0-9_+.-]{1,64}\\.(?:dll|exe))");

    private CharoiteWine29V15ReadOnlyForensics() {}

    private static File exact(File root, String relative) throws Exception {
        File base = root.getCanonicalFile();
        File target = new File(base, relative).getAbsoluteFile();
        if (target.equals(base)
                || !target.getCanonicalFile().toPath().startsWith(base.toPath())
                || !target.getCanonicalFile().equals(target))
            throw new SecurityException("v15 evidence path is linked/outside private scratch");
        return target;
    }

    private static String result(StringBuilder b) {
        String tail = "\nEND OF SHORT V15 READ-ONLY REPORT — raw traces remain on phone, unchanged.\n";
        int limit = MAX_REPORT_CHARS - tail.length();
        if (b.length() > limit) {
            b.setLength(limit - 85);
            b.append("\n[Summary clipped at 9,000 characters; raw evidence NOT deleted.]\n");
        }
        return b.append(tail).toString();
    }

    private static String pid(String line) {
        Matcher m = PID.matcher(line);
        return m.matches() ? m.group(1).toLowerCase(Locale.US) : "unknown";
    }

    private static String safeNames(String line) {
        java.util.LinkedHashSet<String> names = new java.util.LinkedHashSet<>();
        Matcher m = MODULE.matcher(line);
        while (m.find() && names.size() < 4)
            names.add(m.group(1).toLowerCase(Locale.US));
        return names.isEmpty() ? "unspecified" : String.join(", ", names);
    }

    private static String code(String value) {
        try {
            return String.format(Locale.US, "%s (0x%08X)", value,
                (int) Long.parseLong(value));
        } catch (Exception e) {
            return "unparseable";
        }
    }

    private static boolean metadata(File root, StringBuilder out, String path)
            throws Exception {
        File f = exact(root, path);
        boolean present = f.isFile();
        out.append("v15/").append(path).append(": ");
        if (present) out.append("file, contents NOT read");
        else if (f.isDirectory()) out.append("directory, NOT entered");
        else if (!f.exists()) out.append("absent");
        else out.append("unexpected type, NOT entered");
        out.append('\n');
        return present;
    }

    private static void cLink(File scratch, StringBuilder out) {
        File link = new File(scratch, "prefix/dosdevices/c:");
        out.append("v15/prefix/dosdevices/c: ");
        try {
            StructStat st = Os.lstat(link.getAbsolutePath());
            if (!OsConstants.S_ISLNK(st.st_mode)) {
                out.append("NOT a symlink, NOT followed\n");
            } else if ("../drive_c".equals(Os.readlink(link.getAbsolutePath()))) {
                out.append("correct relative symlink, NOT followed\n");
            } else {
                out.append("unexpected target, NOT followed\n");
            }
        } catch (Exception e) {
            out.append("not accessible; NOT created\n");
        }
    }

    /** File metadata only: never open registry contents, follow a link or parse keys. */
    private static long registryBytes(File scratch, String relative) throws Exception {
        File file = exact(scratch, relative);
        return file.isFile() ? file.length() : -1L;
    }

    private static final class Process {
        boolean wineboot, services, scMapped, ntdll, kernel32, apiset, userenv;
        int exits, moduleFailures;
        String firstExit = "none", lastExit = "none";
    }

    private static void peAudit(File scratch, StringBuilder out) throws Exception {
        File log = exact(scratch, PE_LOG);
        if (!log.isFile()) {
            out.append("v15 PE trace absent; no rerun attempted\n");
            return;
        }
        long bytes = log.length();
        if (bytes <= 0 || bytes > MAX_PE_LOG) {
            out.append("v15 PE trace outside 8 MiB read-only bound (")
                .append(bytes).append(" bytes); contents NOT read\n");
            return;
        }
        Map<String,Process> processes = new LinkedHashMap<>();
        ArrayList<String> clues = new ArrayList<>();
        int lines=0, overlong=0, childRequests=0, servicesRequests=0;
        int winebootInitRequests=0, servicesMappings=0, scMappings=0, scRequests=0, userenvMentions=0;
        int moduleErrors=0, dllNotFound=0, exitEvents=0, nonzeroExits=0;
        int regSaves=0, regErrors=0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (++lines > MAX_LINES)
                    throw new SecurityException("v15 PE trace exceeds 100,000 lines");
                if (line.length() > MAX_LINE) { overlong++; continue; }
                String lower = line.toLowerCase(Locale.US);
                String id = pid(line);
                Process process = processes.get(id);
                if (!"unknown".equals(id) && process == null
                        && processes.size() < MAX_PROCESSES) {
                    process = new Process();
                    processes.put(id, process);
                }
                boolean service = lower.contains("services.exe");
                boolean userenv = lower.contains("userenv.dll");
                boolean moduleError = lower.contains("err:module:");
                boolean missing = lower.contains("c0000135") ||
                    lower.contains("status_dll_not_found") ||
                    lower.contains("dll_not_found");
                boolean importError = lower.contains("import_dll")
                    && (lower.contains("failed") || lower.contains("not found"));
                boolean reg = lower.contains("system.reg") || lower.contains("user.reg")
                    || lower.contains("userdef.reg");
                if (userenv) userenvMentions++;
                if (moduleError) moduleErrors++;
                if (missing) dllNotFound++;
                if (reg && (lower.contains("save") || lower.contains("flush"))) regSaves++;
                if (reg && (lower.contains("err:") || lower.contains("failed"))) regErrors++;
                if (lower.contains("ntcreateuserprocess") && lower.contains(" image ")) {
                    childRequests++;
                    if (service) servicesRequests++;
                    if (lower.contains("sc.exe")) scRequests++;
                    if (lower.contains("wineboot.exe") && lower.contains("--init"))
                        winebootInitRequests++;
                }
                if (process != null) {
                    if (moduleError || missing || importError) process.moduleFailures++;
                    if (lower.contains("mapping pe file")) {
                        if (service) {process.services=true; servicesMappings++;}
                        if (lower.contains("sc.exe")) {process.scMapped=true; scMappings++;}
                        if (userenv) process.userenv=true;
                        if (lower.contains("wineboot.exe")) process.wineboot=true;
                        if (lower.contains("ntdll.dll")) process.ntdll=true;
                        if (lower.contains("kernel32.dll")) process.kernel32=true;
                    }
                    if (lower.contains("load_apiset_dll loaded"))
                        process.apiset=true;
                }
                if (clues.size() < 10 &&
                        (moduleError || missing || importError ||
                        (service && (lower.contains("mapping pe file") ||
                        lower.contains("ntcreateuserprocess"))) ||
                        (userenv && (lower.contains("load") || lower.contains("import"))))) {
                    String kind = moduleError ? "module error" :
                        missing ? "DLL_NOT_FOUND" :
                        importError ? "import error" :
                        (service && lower.contains("mapping pe file")) ? "services PE mapped" :
                        service ? "services process requested" : "userenv lookup/load";
                    clues.add("  PE line "+lines+" PID 0x"+id+": "+kind+
                        "; modules="+safeNames(line));
                }
                if (lower.contains("ntterminateprocess") && lower.contains("exit_code")) {
                    Matcher exit = EXIT.matcher(line);
                    if (exit.find()) {
                        exitEvents++;
                        if (!"0".equals(exit.group(1))) nonzeroExits++;
                        if (process != null) {
                            process.exits++;
                            if ("none".equals(process.firstExit))
                                process.firstExit = exit.group(1);
                            process.lastExit = exit.group(1);
                        }
                    }
                }
            }
        }
        out.append("V15 PE TRACE: ").append(bytes).append(" bytes / ").append(lines)
            .append(" lines; overlong skipped=").append(overlong).append('\n');
        out.append("Child-create requests=").append(childRequests)
            .append("; Wineboot --init requests=").append(winebootInitRequests)
            .append("; services.exe requests=").append(servicesRequests)
            .append("; services.exe PE mappings=").append(servicesMappings)
            .append("; sc.exe requests=").append(scRequests)
            .append("; sc.exe mappings=").append(scMappings).append('\n');
        out.append("userenv.dll mentions=").append(userenvMentions)
            .append("; module errors=").append(moduleErrors)
            .append("; DLL_NOT_FOUND markers=").append(dllNotFound).append('\n');
        out.append("PE exit events=").append(exitEvents)
            .append("; nonzero events=").append(nonzeroExits)
            .append("; registry save/flush references=").append(regSaves)
            .append("; registry error references=").append(regErrors).append('\n');
        for (Map.Entry<String,Process> e : processes.entrySet()) {
            Process p=e.getValue();
            if (!p.wineboot && !p.services && !p.scMapped && p.exits==0 && p.moduleFailures==0)
                continue;
            out.append("PE PID 0x").append(e.getKey())
                .append(": wineboot=").append(p.wineboot)
                .append(" services=").append(p.services)
                .append(" sc_mapped=").append(p.scMapped)
                .append(" userenv_mapped=").append(p.userenv)
                .append(" ntdll=").append(p.ntdll)
                .append(" kernel32=").append(p.kernel32)
                .append(" apiset=").append(p.apiset)
                .append(" failures=").append(p.moduleFailures)
                .append(" exits=").append(p.exits)
                .append(" first=").append(code(p.firstExit))
                .append(" last=").append(code(p.lastExit)).append('\n');
        }
        int servicesPids=0, servicesWithUserenv=0, servicesWithErrors=0;
        int servicesExitEvents=0;
        for (Process p : processes.values()) {
            if (!p.services) continue;
            servicesPids++;
            if (p.userenv) servicesWithUserenv++;
            if (p.moduleFailures > 0) servicesWithErrors++;
            servicesExitEvents += p.exits;
        }
        out.append("SERVICES PE LIFECYCLE: mapped PIDs=").append(servicesPids)
            .append("; with userenv mapped=").append(servicesWithUserenv)
            .append("; with observed module failures=").append(servicesWithErrors)
            .append("; observed PE exit events=").append(servicesExitEvents).append('\n');
        if (servicesPids > 0 && servicesExitEvents == 0)
            out.append("No services PE exit observed in retained log; this does NOT prove ")
                .append("the service remains running or SCM initialized.\n");
        out.append("First 10 relevant PE event TYPES (no raw log text/paths):\n");
        if (clues.isEmpty()) out.append("  no targeted module or services events observed\n");
        for (String s : clues) out.append(s).append('\n');
    }

    private static void serverAudit(File scratch, StringBuilder out) throws Exception {
        File log = exact(scratch, SERVER_LOG);
        if (!log.isFile()) {
            out.append("v15 server trace absent; no server launched\n");
            return;
        }
        long bytes=log.length();
        if (bytes <= 0 || bytes > MAX_SERVER_LOG) {
            out.append("v15 server trace outside 8 MiB read-only bound (")
                .append(bytes).append(" bytes); contents NOT read\n");
            return;
        }
        int lines=0, overlong=0, starts=0, newRequests=0, newReplies=0;
        int serviceMentions=0, scMentions=0, statusMissing=0, regOperations=0, regFailures=0;
        int threadEvents=0, shutdown=0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(log), StandardCharsets.UTF_8), 16384)) {
            String line;
            while ((line=reader.readLine())!=null) {
                if (++lines>MAX_LINES)
                    throw new SecurityException("v15 server trace exceeds 100,000 lines");
                if (line.length()>MAX_LINE) {overlong++;continue;}
                String lower=line.toLowerCase(Locale.US);
                if (lower.contains("wineserver: starting")) starts++;
                if (lower.contains("new_process(") && !lower.contains("new_process()"))
                    newRequests++;
                if (lower.contains("new_process() =")) newReplies++;
                if (lower.contains("init_first_thread")) threadEvents++;
                if (lower.contains("services.exe")) serviceMentions++;
                if (lower.contains("sc.exe")) scMentions++;
                if (lower.contains("c0000135") || lower.contains("dll_not_found"))
                    statusMissing++;
                if (lower.contains("save_registry") || lower.contains("flush_registry")
                        || lower.contains("system.reg") || lower.contains("user.reg")
                        || lower.contains("userdef.reg")) {
                    regOperations++;
                    if (lower.contains("failed") || lower.contains("error")
                            || lower.contains("access_denied"))
                        regFailures++;
                }
                if (lower.contains("shutdown") || lower.contains("server: exiting"))
                    shutdown++;
            }
        }
        out.append("V15 SERVER TRACE: ").append(bytes).append(" bytes / ").append(lines)
            .append(" lines; overlong skipped=").append(overlong).append('\n');
        out.append("Server starts=").append(starts)
            .append("; process requests=").append(newRequests)
            .append("; process replies=").append(newReplies)
            .append("; first-thread mentions=").append(threadEvents)
            .append("; services.exe mentions=").append(serviceMentions)
            .append("; sc.exe mentions=").append(scMentions).append('\n');
        out.append("Server DLL_NOT_FOUND markers=").append(statusMissing)
            .append("; registry references=").append(regOperations)
            .append("; registry failure references=").append(regFailures)
            .append("; shutdown mentions=").append(shutdown).append('\n');
        out.append("V15 foreground wineserver was alive before separate sc.exe launch, ")
            .append("but not alive immediately afterward (owner execution report). ")
            .append("Server trace shutdown markers are counts, NOT causal proof; ")
            .append("look for independent sc.exe new_process events without attributing an exit.\n");
    }



    /** V15 Windows-path sc.exe was attempted once; NOT an SCM query audit. */
    private static void entryAudit(File scratch, StringBuilder out) throws Exception {
        File f=exact(scratch,ENTRY_LOG);
        if(!f.isFile()){out.append("V15 sc.exe entry log: absent; no PE-entry proof\n");return;}
        long bytes=f.length();
        out.append("V15 sc.exe entry log bytes=").append(bytes).append("; ");
        if(bytes==0||bytes>MAX_SC_LOG){
            out.append(bytes==0 ? "EMPTY; no retained stdout/stderr, PE mapping NOT VERIFIED\n"
                                  : "above 8 MiB cap; contents NOT read\n");return;
        }
        int lines=0,overlong=0,mapped=0,usage=0,missing=0;
        try(BufferedReader r=new BufferedReader(new InputStreamReader(
                new FileInputStream(f),StandardCharsets.UTF_8),16384)){
            String line;
            while((line=r.readLine())!=null){
                if(++lines>MAX_LINES)throw new SecurityException("V15 entry log line cap");
                if(line.length()>MAX_LINE){overlong++;continue;}
                String lower=line.toLowerCase(Locale.US);
                if(lower.contains("mapping pe file")&&lower.contains("sc.exe"))mapped++;
                if(lower.contains("usage:")||lower.contains("description:"))usage++;
                if(lower.contains("c0000135")||lower.contains("dll_not_found"))missing++;
            }
        }
        out.append(lines).append(" lines; overlong=").append(overlong)
            .append("; sc PE map markers=").append(mapped)
            .append("; usage hints=").append(usage)
            .append("; missing DLL markers=").append(missing).append('\n');
        out.append("Usage or exit status alone is NOT PE-mapping proof or SCM readiness.\n");
    }


    public static String run(Context context){
        StringBuilder out=new StringBuilder();
        out.append("CHAROITE NEXT — WINE29 V15 PRESERVED SC.EXE PE-ENTRY POSTMORTEM\n");
        out.append("STRICT READ ONLY: no Wine/Wineboot/sc.exe/services.exe/wineserver, ")
            .append("process creation, retries, scratch creation, writes or cleanup.\n");
        out.append("Only THREE V15 logs and explicitly named V15 metadata; no V1–V14, ")
            .append("Wine28, stable Portal, games, saves, user prefixes or rootfs.\n");
        if(!PACKAGE.equals(context.getPackageName())||Build.VERSION.SDK_INT<26){
            out.append("RESULT: BLOCKED — package/Android safety gate\n");
            return result(out);
        }
        try{
            File base=context.getNoBackupFilesDir().getCanonicalFile();
            File scratch=exact(base,SCRATCH);
            if(!scratch.isDirectory()){
                out.append("RESULT: BLOCKED — V15 scratch absent; NOT created\n");
                return result(out);
            }
            out.append("Previously used V15 scratch: present, untouched\n");
            cLink(scratch,out);
            for(String name:new String[]{
                    "prefix/drive_c","prefix/drive_c/windows",
                    "prefix/drive_c/windows/system32","prefix/drive_c/users",
                    "prefix/drive_c/users/xuser/AppData","prefix/drive_c/Program Files",
                    "runtime/lib/wine/aarch64-windows/wineboot.exe",
                    "runtime/lib/wine/aarch64-windows/services.exe",
                    "runtime/lib/wine/aarch64-windows/userenv.dll",
                    "runtime/lib/wine/aarch64-windows/sc.exe",
                    "prefix/drive_c/windows/system32/sc.exe"})
                metadata(scratch,out,name);
            boolean sys=metadata(scratch,out,"prefix/system.reg");
            boolean usr=metadata(scratch,out,"prefix/user.reg");
            boolean def=metadata(scratch,out,"prefix/userdef.reg");
            long a=registryBytes(scratch,"prefix/system.reg");
            long b=registryBytes(scratch,"prefix/user.reg");
            long d=registryBytes(scratch,"prefix/userdef.reg");
            out.append("Registry sizes (metadata ONLY): system=").append(a)
               .append(" B, user=").append(b).append(" B, userdef=").append(d)
               .append(" B; contents NOT opened\n");
            out.append("Three registry files nonempty=").append(sys&&usr&&def&&a>0&&b>0&&d>0)
               .append("; registry completeness and SCM NOT verified\n");
            try{peAudit(scratch,out);}
            catch(SecurityException e){out.append("PE audit bounded/blocked: ")
                .append(e.getMessage()).append("; no retries/writes\n");}
            try{entryAudit(scratch,out);}
            catch(SecurityException e){out.append("Entry audit bounded/blocked: ")
                .append(e.getMessage()).append("; no retries/writes\n");}
            try{serverAudit(scratch,out);}
            catch(SecurityException e){out.append("Server audit bounded/blocked: ")
                .append(e.getMessage()).append("; no retries/writes\n");}
            out.append("RESULT: READ-ONLY V15 AUDIT COMPLETE. Source report records ")
               .append("one Windows C: path sc.exe attempt, exit 127/zero output, NOEXEC=1; ")
               .append("server alive before sc.exe but NOT alive immediately after. Counts here are bounded ")
               .append("trace observations, not proof of missing PE mapping, a diagnosed ")
               .append("exit-127 cause or SCM/gaming readiness. NOEXEC=1 ") 
               .append("did not resolve exit 127; Windows C: path with NOEXEC=1 did not resolve exit 127. The server disappearance is an observation, NOT proof of a sc.exe crash or root cause. NO replay or cleanup.\n");
            out.append("Pre-shutdown registry booleans are time-specific; the three ")
               .append("post-shutdown sizes above are metadata only, NOT a prefix integrity check.\n");
            out.append("No Windows PE or games executed by this read-only audit.\n");
            out.append("Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md\n");
        }catch(Exception e){
            out.append("RESULT: BLOCKED — ").append(e.getClass().getSimpleName())
               .append("; preserved V15 evidence unchanged\n");
        }
        return result(out);
    }
}
