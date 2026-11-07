package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Explicitly confirmed one-shot Wine29 v2 bootstrap-mode investigation. Without explicit user opt-in, no process is run.
 * Wine may automatically run its own first-use wineboot --init before processing
 * the requested --help argument. This is allowed ONLY inside brand-new v2 scratch.
 * NEVER accesses any pre-existing prefix, rootfs, game, save or legacy cohort.
 * Only a brand-new v2 noBackupFilesDir child is writable; it is never erased
 * automatically, even after failure. A failed attempt requires diagnosis before
 * another generation may be authorized.
 */
public final class CharoiteWine29V2BootstrapProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String STAGE_ROOT = "charoite-next-wine29-012-sealed-pe-nls/wine10-arm64ec-dependencies-0.12-sealed-pe-nls";
    private static final String SCRATCH = "charoite-next-wine29-bootstrap-v2";
    private static final String INDEX = "charoite-next/wine29-sealed012/wine29-sealed012-index.json";
    private static final String NATIVE_LOADER = "libcharoite_wine29_loader.so";
    private static final String NATIVE_SERVER = "libcharoite_wine29_wineserver.so";
    private static final int COUNT = 111;
    private static final long LIMIT = 128L * 1024L * 1024L;
    private static final long TIMEOUT = 25L;
    private static final long MAX_LOG = 8L * 1024L * 1024L;
    private CharoiteWine29V2BootstrapProbe() {}

    private static File child(File parent, String name) throws Exception {
        File base = parent.getCanonicalFile();
        File file = new File(base, name);
        if (!file.getCanonicalFile().toPath().startsWith(base.toPath())
                || file.getCanonicalFile().equals(base))
            throw new SecurityException("Wine29 path escapes isolated private directory");
        return file;
    }

    private static void mkdir(File dir) throws Exception {
        if ((!dir.exists() && !dir.mkdirs()) || !dir.isDirectory()
                || !dir.getCanonicalFile().equals(dir.getAbsoluteFile()))
            throw new SecurityException("Wine29 scratch directory is unsafe");
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder();
        for (byte b:bytes)
            out.append(String.format(Locale.US, "%02x", b & 255));
        return out.toString();
    }

    private static void copyVerified(File src, File dst, long size, String sha)
            throws Exception {
        if (!src.isFile() || size <= 0 || size > 32L*1024*1024
                || src.length() != size || dst.exists()
                || !src.getCanonicalFile().equals(src.getAbsoluteFile()))
            throw new SecurityException("Unsafe staged Wine29 module");
        mkdir(dst.getParentFile());
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        long count = 0;
        try (InputStream input = new FileInputStream(src);
             FileOutputStream output = new FileOutputStream(dst)) {
            byte[] block = new byte[32768];
            int n;
            while ((n = input.read(block)) != -1) {
                count += n;
                if (count > size)
                    throw new SecurityException("Wine29 copy exceeds source size");
                md.update(block, 0, n);
                output.write(block, 0, n);
            }
            output.getFD().sync();
        }
        if (count != size || !sha.equals(hex(md.digest())))
            throw new SecurityException("Wine29 scratch module source SHA mismatch");
    }

    private static Map<String,String> cleanEnv(ProcessBuilder pb,
            File nativeDir, File server, File scratch, File prefix, File library)
            throws Exception {
        Map<String,String> env = pb.environment();
        env.clear();
        env.put("PATH", "/system/bin:/system/xbin");
        env.put("HOME", child(scratch,"home").getCanonicalPath());
        env.put("TMPDIR", child(scratch,"tmp").getCanonicalPath());
        env.put("TMP", child(scratch,"tmp").getCanonicalPath());
        env.put("TEMP", child(scratch,"tmp").getCanonicalPath());
        env.put("XDG_CACHE_HOME", child(scratch,"cache").getCanonicalPath());
        env.put("XDG_CONFIG_HOME", child(scratch,"config").getCanonicalPath());
        env.put("XDG_RUNTIME_DIR", child(scratch,"xdg-runtime").getCanonicalPath());
        env.put("WINEPREFIX", prefix.getCanonicalPath());
        env.put("WINEARCH", "win64");
        env.put("WINEDEBUG", "-all,err+all,+loaddll,+module,+process,+seh,+server,+file");
        // Do NOT globally force bootstrap mode. Wine controls it during internal --init.
        if (env.containsKey("WINEBOOTSTRAPMODE"))
            throw new SecurityException("Bootstrap mode leaked into explicit help environment");
        // Wine 10 ntdll can re-exec an unavailable Wine bin-directory loader.
        // Disable that secondary handoff only in this dedicated v2 trace.
        env.put("WINELOADERNOEXEC", "1");
        env.put("WINESERVER", server.getCanonicalPath());
        // Wine's ARM64 get_pe_dir() appends /aarch64-windows to each search ROOT.
        // Previous v7 mistakenly supplied a directory of PE DLLs directly.
        // The v2 scratch uses the correct root and directory layout.
        env.put("WINEDLLPATH", child(scratch,"runtime/lib/wine").getCanonicalPath());
        env.put("CHAROITE_WINE29_NATIVE_DIR", nativeDir.getCanonicalPath());
        // Initial PE NTDLL lookup, before ordinary WINEDLLPATH DLL resolution.
        // The 111 PE/NLS files were copied with SHA-256 verification in v2 only.
        File peNtdll = child(library,"ntdll.dll");
        if (!peNtdll.isFile()
                || !peNtdll.getCanonicalFile().equals(peNtdll.getAbsoluteFile()))
            throw new SecurityException("Wine29 verified Windows NTDLL PE absent");
        env.put("CHAROITE_WINE29_PE_DIR", library.getCanonicalPath());
        // Native Wine 10 ntdll and wineserver must use the new, verified
        // scratch-local NLS directory, never the read-only APK library tree.
        File dataDir = child(scratch,"runtime/share/wine");
        if (!child(dataDir,"nls/locale.nls").isFile()
                || !child(dataDir,"nls/l_intl.nls").isFile())
            throw new SecurityException("Fresh Wine29 NLS layout incomplete");
        env.put("CHAROITE_WINE29_DATA_DIR", dataDir.getCanonicalPath());
        env.put("LC_ALL", "C");
        return env;
    }

    private static String sanitizeLog(String value, File root) {
        StringBuilder safe = new StringBuilder();
        String prefix = root.getAbsolutePath();
        for (String line : value.split("\\n", -1)) {
            String lower = line.toLowerCase(Locale.US);
            if (lower.contains("env=") || lower.contains("password")
                    || lower.contains("secret") || lower.contains("token=")) {
                safe.append("[redacted sensitive process line]\\n");
                continue;
            }
            String cleaned = line.replace(prefix, "[v2-private-scratch]")
                    .replace('\\r', ' ').replace('\\0', ' ');
            safe.append(cleaned.length() > 760 ? cleaned.substring(0, 760) + " [clipped]" : cleaned).append('\\n');
            if (safe.length() >= 16000) break;
        }
        return safe.toString();
    }

    private static String boundedLog(File file) throws Exception {
        if (!file.isFile()) return "(no process output)";
        long size = file.length();
        if (size == 0) return "(empty)";
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            if (size <= 12288) {
                byte[] full = new byte[(int) size];
                input.readFully(full);
                return sanitizeLog(new String(full, "UTF-8"), file.getParentFile());
            }
            byte[] head = new byte[6144];
            byte[] tail = new byte[6144];
            input.readFully(head);
            input.seek(size - tail.length);
            input.readFully(tail);
            return sanitizeLog(new String(head,"UTF-8")
                + "\n[... skipped middle of " + size + " bytes ...]\n"
                + new String(tail,"UTF-8"), file.getParentFile());
        }
    }


    private static boolean[] socketAndLock(File prefix) throws Exception {
        File top = child(prefix, ".wineserver");
        boolean[] observed = new boolean[]{false, false};
        if (!top.isDirectory() || !top.getCanonicalFile().equals(top.getAbsoluteFile()))
            return observed;
        File[] entries = top.listFiles();
        if (entries == null) return observed;
        int count = 0;
        for (File dir:entries) {
            if (count++ >= 16) break;
            if (!dir.getName().matches("server-[0-9a-f]+-[0-9a-f]+")
                    || !dir.getCanonicalFile().equals(dir.getAbsoluteFile())
                    || !dir.isDirectory()) continue;
            for (String name:new String[]{"socket","lock"}) {
                File candidate = child(dir,name);
                try {
                    StructStat stat = Os.lstat(candidate.getAbsolutePath());
                    if ("socket".equals(name) && OsConstants.S_ISSOCK(stat.st_mode))
                        observed[0] = true;
                    if ("lock".equals(name) && OsConstants.S_ISREG(stat.st_mode))
                        observed[1] = true;
                } catch (android.system.ErrnoException ignored) {
                    // A missing socket or lock is not a positive result.
                }
            }
        }
        return observed;
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — NEW ISOLATED WINE29 V2 BOOTSTRAP / KERNEL32 TRACE\n");
        out.append("Explicit one-shot; NEW v2 scratch; explicit wineboot --help; Wine WILL attempt internal auto --init in NEW v2 prefix\n");
        out.append("Source-built foreground server then matched ARM64 wineboot.exe --help ONLY\n");
        out.append("Wine28 v1–v9, stable Portal, user prefixes/games/saves/rootfs: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return out.append("RESULT: BLOCKED — unsupported package/device\n").toString();
        String preflight = CharoiteWine29Sealed012PePreflight.run(context);
        if (!preflight.contains("RESULT: PASS — isolated Wine29 0.12 34-DLL direct/delay PE preflight; NOT RUNNABLE"))
            return out.append("RESULT: BLOCKED — sealed Wine29 34-DLL PE import preflight failed; NO new scratch\n")
                .append(preflight).toString();
        out.append("Wine29 34-DLL header/ordinary/delay import preflight: PASS\n");
        String gate = CharoiteWine29Sealed012Stage.verifyOnly(context);
        if (!gate.contains("RESULT: PASS — isolated Wine29 0.12 data-only stage; NOT RUNNABLE"))
            return out.append("RESULT: BLOCKED — matched Wine29 111-file source/PE/NLS/native SHA-256 gate failed\n")
                .append(gate).toString();
        out.append("Wine29 staged 111 PE/NLS and APK-native three ELF hashes: PASS\n");

        Process serverProc = null, peProc = null;
        File serverLog = null, peLog = null;
        File scratch = null;
        try {
            File privateBase = context.getNoBackupFilesDir().getCanonicalFile();
            File staged = child(privateBase, STAGE_ROOT);
            if (!staged.isDirectory()) throw new SecurityException("Wine29 stage absent");
            scratch = child(privateBase, SCRATCH);
            if (scratch.exists() || !scratch.mkdir())
                throw new SecurityException("V2 one-shot scratch already exists or unavailable; NO retry");
            if (!scratch.getCanonicalFile().getParentFile().equals(privateBase))
                throw new SecurityException("V2 private scratch parent changed");
            File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            File loader = child(nativeDir,NATIVE_LOADER);
            File server = child(nativeDir,NATIVE_SERVER);
            if (!loader.isFile() || !server.isFile()
                    || !loader.getCanonicalFile().equals(loader.getAbsoluteFile())
                    || !server.getCanonicalFile().equals(server.getAbsoluteFile()))
                throw new SecurityException("Source-matched native launcher/server absent");
            File lib = child(scratch,"runtime/lib/wine/aarch64-windows");
            File boot = child(scratch,"runtime/lib/wine/arm64-windows/wineboot.exe");
            ByteArrayOutputStream blob = new ByteArrayOutputStream();
            try (InputStream input = context.getAssets().open(INDEX)) {
                byte[] block = new byte[4096]; int n;
                while ((n = input.read(block)) != -1) {
                    if (blob.size()+n > 65536)
                        throw new SecurityException("Wine29 index too large");
                    blob.write(block,0,n);
                }
            }
            JSONObject index = new JSONObject(blob.toString("UTF-8"));
            JSONArray modules = index.getJSONArray("module_files");
            if (modules.length() != COUNT || index.getInt("pe_count") != 35
                    || index.getInt("nls_count") != 76
                    || index.getInt("component_count") != 35
                    || index.getInt("module_count") != 111
                    || index.getInt("native_elf_count") != 3
                    || !"wine10-arm64ec-dependencies.0.12-sealed-data-candidate".equals(
                        index.getString("bundle_version"))
                    || !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(
                        index.getString("wine_source_commit"))
                    || index.getBoolean("launch_ready"))
                throw new SecurityException("Wine29 source index mismatch");
            int dll=0, nls=0, exe=0;
            long total=0;
            for (int i=0; i<modules.length();i++) total+=modules.getJSONObject(i).getLong("size");
            if (total < 1 || total > LIMIT
                    || privateBase.getUsableSpace() < 2*total + 64L*1024*1024)
                throw new SecurityException("Insufficient scratch-only capacity");
            for (int i=0;i<modules.length();i++) {
                JSONObject m=modules.getJSONObject(i);
                String name=m.getString("path");
                File dst;
                if (name.matches("pe/arm64ec/[a-z0-9_]+\\.dll")) {
                    dst=child(lib,name.substring("pe/arm64ec/".length())); dll++;
                } else if (name.equals("pe/arm64/wineboot.exe")) {
                    dst=boot; exe++;
                } else if (name.matches("nls/[a-z0-9_]+\\.nls")) {
                    dst=child(scratch,"runtime/share/wine/"+name); nls++;
                } else throw new SecurityException("Unexpected Wine29 module");
                copyVerified(child(staged,name),dst,m.getLong("size"),m.getString("sha256"));
                if (name.equals("pe/arm64/wineboot.exe")) {
                    // Wine first auto-starts C:\\windows\\system32\\wineboot.exe --init.
                    // Its ARM64 builtin search is under WINEDLLDIR0/aarch64-windows.
                    // Copy the EXACT verified source into that leaf as well as boot.
                    copyVerified(child(staged,name),child(lib,"wineboot.exe"),
                                 m.getLong("size"),m.getString("sha256"));
                }
            }
            if (dll!=34 || exe!=1 || nls!=76 || !boot.isFile())
                throw new SecurityException("Wine29 verified scratch inventory incomplete");
            out.append("Fresh v2 scratch: 34 hybrid DLLs + ARM64 wineboot.exe + 76 NLS hashes PASS\n");
            File bootBuiltin=child(lib,"wineboot.exe");
            if (!bootBuiltin.isFile()
                    || !bootBuiltin.getCanonicalFile().equals(bootBuiltin.getAbsoluteFile())
                    || bootBuiltin.length()!=boot.length())
                throw new SecurityException("V2 source-matched builtin Wineboot alias missing");
            out.append("V2 built-in auto-init Wineboot copy: ")
                .append("aarch64-windows/wineboot.exe SHA-256 PASS\n");
            File rootDir=child(scratch,"runtime/lib/wine");
            File kernel=child(lib,"kernel32.dll");
            if (!kernel.isFile() || !kernel.getCanonicalFile().equals(kernel.getAbsoluteFile()))
                throw new SecurityException("V2 ARM64 kernel32 file absent from Wine lookup layout");
            out.append("V2 PE machine lookup: ARM64, search suffix /aarch64-windows\n");
            out.append("V2 WINEDLLPATH: ").append(rootDir.getCanonicalPath()).append('\n');
            out.append("V2 kernel32 PE: verified aarch64-windows/kernel32.dll present\n");
            out.append("V2 prior Wine28 PE directory layout: not accessed; independent new scratch\n");
            File prefix=child(scratch,"prefix");
            mkdir(prefix);
            for (String p:new String[]{"home","tmp","cache","config","xdg-runtime"})
                mkdir(child(scratch,p));
            // Although no explicit -i is requested, Wine itself may run automatic --init inside v2.
            // A foreground server supplies a known-good socket before PE startup.
            serverLog=child(scratch,"v2-foreground-wineserver.log");
            ProcessBuilder s=new ProcessBuilder(server.getAbsolutePath(),"-f","-d");
            s.directory(scratch);
            s.redirectErrorStream(true);
            s.redirectOutput(serverLog);
            cleanEnv(s,nativeDir,server,scratch,prefix,lib);
            serverProc=s.start();
            boolean[] live=new boolean[]{false,false};
            boolean serverTimedOut=false, serverOverflow=false;
            long begin=System.nanoTime();
            while (serverProc.isAlive()) {
                boolean[] observed=socketAndLock(prefix);
                live[0]|=observed[0]; live[1]|=observed[1];
                if (live[0]&&live[1]) break;
                if (serverLog.length()>262144L) {serverOverflow=true;break;}
                if (System.nanoTime()-begin > TimeUnit.SECONDS.toNanos(5)) {serverTimedOut=true;break;}
                serverProc.waitFor(100,TimeUnit.MILLISECONDS);
            }
            out.append("V2 foreground wineserver socket observed: ").append(live[0]).append('\n');
            out.append("V2 foreground wineserver lock observed: ").append(live[1]).append('\n');
            out.append("V2 foreground server startup timeout: ").append(serverTimedOut).append('\n');
            out.append("V2 foreground server log cap exceeded: ").append(serverOverflow).append('\n');
            if (live[0]&&live[1]&&serverProc.isAlive()&&!serverOverflow) {
                peLog=child(scratch,"v2-wine-pe-help.log");
                ProcessBuilder p=new ProcessBuilder(loader.getAbsolutePath(),
                                                   boot.getAbsolutePath(),"--help");
                p.directory(scratch);
                p.redirectErrorStream(true);
                p.redirectOutput(peLog);
                Map<String,String> helpEnv = cleanEnv(p,nativeDir,server,scratch,prefix,lib);
                if (helpEnv.containsKey("WINEBOOTSTRAPMODE"))
                    throw new SecurityException("Explicit Wineboot help inherited bootstrap mode");
                out.append("V2 help launcher WINEBOOTSTRAPMODE: UNSET (verified)\\n");
                out.append("Wine may temporarily enable bootstrap mode for internal auto --init; no override is installed\\n");
                peProc=p.start();
                boolean finished=false, expired=false, overflow=false;
                int exit=-999;
                long start=System.nanoTime();
                while (!finished && !expired && !overflow) {
                    finished=peProc.waitFor(200,TimeUnit.MILLISECONDS);
                    if (finished) exit=peProc.exitValue();
                    overflow=peLog.length()>2L*1024L*1024L;
                    expired=System.nanoTime()-start>=TimeUnit.SECONDS.toNanos(12);
                }
                if (peProc.isAlive()) {
                    peProc.destroyForcibly();
                    peProc.waitFor(2,TimeUnit.SECONDS);
                }
                String peText=boundedLog(peLog);
                boolean help=peText.contains("Usage: wineboot");
                out.append("V2 PE trace kernel32.dll mentioned: ").append(peText.toLowerCase(Locale.US).contains("kernel32.dll")).append('\\n');
                out.append("V2 PE trace c0000135 seen: ").append(peText.toLowerCase(Locale.US).contains("c0000135")).append('\\n');
                out.append("V2 PE trace bootstrap-mode text seen: ").append(peText.contains("WINEBOOTSTRAPMODE")).append(" (absence not proof of mode)\\n");
                out.append("Windows PE attempted: true (wineboot.exe --help ONLY; never -i)\n");
                out.append("PE process completed within 12s: ").append(finished).append('\n');
                out.append("PE exit code: ").append(finished?Integer.toString(exit):"BOUNDED STOP").append('\n');
                out.append("PE 12s deadline exceeded: ").append(expired).append('\n');
                out.append("PE log 2MiB cap exceeded: ").append(overflow).append('\n');
                out.append("Wineboot PE help marker observed: ").append(help).append('\n');
                out.append("Foreground server alive after PE process: ").append(serverProc.isAlive()).append('\n');
                out.append("PE loader output bounded:\n").append(peText).append('\n');
                if (finished&&exit==0&&help&&!expired&&!overflow)
                    out.append("RESULT: PASS — isolated Wine29 PE help reached; NOT Wineboot -i or Windows gaming\n");
                else
                    out.append("RESULT: FAIL — isolated Wine29 PE help did not complete; inspect preserved v2 logs\n");
            } else {
                out.append("Windows PE attempted: false — foreground server was not ready\n");
                out.append("RESULT: FAIL — v2 server handshake unavailable; no PE execution\n");
            }
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — ").append(e.getClass().getSimpleName())
               .append(": ").append(e.getMessage()).append('\n');
        } finally {
            try {
                if (peProc!=null&&peProc.isAlive()) {
                    peProc.destroyForcibly(); peProc.waitFor(2,TimeUnit.SECONDS);
                }
                if (serverProc!=null&&serverProc.isAlive()) {
                    serverProc.destroyForcibly(); serverProc.waitFor(2,TimeUnit.SECONDS);
                }
                out.append("Foreground v2 server terminated if running; no other prefix/server targeted\n");
                if (serverLog!=null)
                    String serverText=boundedLog(serverLog);
                    out.append("V2 server trace internal auto-init marker observed: ")
                       .append(serverText.contains("--init")).append(" (absence not proof it did not run)\\n");
                    out.append("V2 server debug log bounded and redacted:\\n").append(serverText).append('\\n');
            } catch (Exception e) {
                out.append("V2 cleanup/reading diagnostics: ")
                   .append(e.getClass().getSimpleName()).append('\n');
            }
        }
        out.append("V2 one-shot scratch retained; NEVER rerun/delete v2 after first use\n");
        out.append("Wine28 v1–v9, stable Portal, old Wine29 staging, original Wine and game saves: UNCHANGED\n");
        return out.toString();
    }
}
