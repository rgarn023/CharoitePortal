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
 * User-confirmed, one-shot Wine28 PE --help diagnostic only; never perform prefix initialization.
 * NEVER accesses any pre-existing prefix, rootfs, game, save or legacy cohort.
 * Only a brand-new v7 noBackupFilesDir child is writable; it is never erased
 * automatically, even after failure. A failed attempt requires diagnosis before
 * another generation may be authorized.
 */
public final class CharoiteWine28V7PeHelpProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String STAGE_ROOT = "charoite-next-isolated-wine/wine10-arm64ec-bootstrap-0.7-staged";
    private static final String SCRATCH = "charoite-next-wine28-pe-help-v7";
    private static final String INDEX = "charoite-next/wine-bootstrap-28-index.json";
    private static final String NATIVE_LOADER = "libcharoite_wine28_loader.so";
    private static final String NATIVE_SERVER = "libcharoite_wine28_wineserver.so";
    private static final int COUNT = 99;
    private static final long LIMIT = 128L * 1024L * 1024L;
    private static final long TIMEOUT = 25L;
    private static final long MAX_LOG = 8L * 1024L * 1024L;
    private CharoiteWine28V7PeHelpProbe() {}

    private static File child(File parent, String name) throws Exception {
        File base = parent.getCanonicalFile();
        File file = new File(base, name);
        if (!file.getCanonicalFile().toPath().startsWith(base.toPath())
                || file.getCanonicalFile().equals(base))
            throw new SecurityException("Wine28 path escapes isolated private directory");
        return file;
    }

    private static void mkdir(File dir) throws Exception {
        if ((!dir.exists() && !dir.mkdirs()) || !dir.isDirectory()
                || !dir.getCanonicalFile().equals(dir.getAbsoluteFile()))
            throw new SecurityException("Wine28 scratch directory is unsafe");
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
            throw new SecurityException("Unsafe staged Wine28 module");
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
                    throw new SecurityException("Wine28 copy exceeds source size");
                md.update(block, 0, n);
                output.write(block, 0, n);
            }
            output.getFD().sync();
        }
        if (count != size || !sha.equals(hex(md.digest())))
            throw new SecurityException("Wine28 scratch module source SHA mismatch");
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
        env.put("WINEDEBUG", "-all,err+all,+loaddll,+module,+process,+seh,+server");
        // Wine 10 ntdll can re-exec an unavailable Wine bin-directory loader.
        // Disable that secondary handoff only in this dedicated v7 trace.
        env.put("WINELOADERNOEXEC", "1");
        env.put("WINESERVER", server.getCanonicalPath());
        env.put("WINEDLLPATH", library.getCanonicalPath()
                + ":" + child(scratch,"runtime/lib/wine/arm64-windows").getCanonicalPath());
        env.put("CHAROITE_WINE28_NATIVE_DIR", nativeDir.getCanonicalPath());
        // Initial PE NTDLL lookup, before ordinary WINEDLLPATH DLL resolution.
        // The 99 PE/NLS files were copied with SHA-256 verification in v7 only.
        File peNtdll = child(library,"ntdll.dll");
        if (!peNtdll.isFile()
                || !peNtdll.getCanonicalFile().equals(peNtdll.getAbsoluteFile()))
            throw new SecurityException("Wine28 verified Windows NTDLL PE absent");
        env.put("CHAROITE_WINE28_PE_DIR", library.getCanonicalPath());
        // Native Wine 10 ntdll and wineserver must use the new, verified
        // scratch-local NLS directory, never the read-only APK library tree.
        File dataDir = child(scratch,"runtime/share/wine");
        if (!child(dataDir,"nls/locale.nls").isFile()
                || !child(dataDir,"nls/l_intl.nls").isFile())
            throw new SecurityException("Fresh Wine28 NLS layout incomplete");
        env.put("CHAROITE_WINE26_DATA_DIR", dataDir.getCanonicalPath());
        env.put("LC_ALL", "C");
        return env;
    }

    private static String boundedLog(File file) throws Exception {
        if (!file.isFile()) return "(no process output)";
        long size = file.length();
        if (size == 0) return "(empty)";
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            if (size <= 12288) {
                byte[] full = new byte[(int) size];
                input.readFully(full);
                return new String(full, "UTF-8");
            }
            byte[] head = new byte[6144];
            byte[] tail = new byte[6144];
            input.readFully(head);
            input.seek(size - tail.length);
            input.readFully(tail);
            return new String(head,"UTF-8")
                + "\n[... skipped middle of " + size + " bytes ...]\n"
                + new String(tail,"UTF-8");
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
        out.append("CHAROITE NEXT — NEW ISOLATED WINE28 V7 PE-HELP HANDSHAKE\n");
        out.append("Explicit one-shot; NEW v7 scratch; not Wineboot -i or prefix initialization\n");
        out.append("Source-built foreground server then matched ARM64 wineboot.exe --help ONLY\n");
        out.append("Wine22, Portal, user prefixes/games/saves/rootfs and v1-v6: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return out.append("RESULT: BLOCKED — unsupported package/device\n").toString();
        String gate = CharoiteWine28NativeGate.run(context);
        if (!gate.contains("RESULT: PASS — matched Wine28 native --version gate; NOT runnable"))
            return out.append("RESULT: BLOCKED — matched Wine28 source/native gate failed\n")
                .append(gate).toString();
        out.append("Wine28 staged 99 hashes, native three hashes, version-only probes: PASS\n");
        Process serverProc = null, peProc = null;
        File serverLog = null, peLog = null;
        File scratch = null;
        try {
            File privateBase = context.getNoBackupFilesDir().getCanonicalFile();
            File staged = child(privateBase, STAGE_ROOT);
            if (!staged.isDirectory()) throw new SecurityException("Wine28 stage absent");
            scratch = child(privateBase, SCRATCH);
            if (scratch.exists() || !scratch.mkdir())
                throw new SecurityException("V7 one-shot scratch already exists or unavailable; NO retry");
            if (!scratch.getCanonicalFile().getParentFile().equals(privateBase))
                throw new SecurityException("V7 private scratch parent changed");
            File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            File loader = child(nativeDir,NATIVE_LOADER);
            File server = child(nativeDir,NATIVE_SERVER);
            if (!loader.isFile() || !server.isFile()
                    || !loader.getCanonicalFile().equals(loader.getAbsoluteFile())
                    || !server.getCanonicalFile().equals(server.getAbsoluteFile()))
                throw new SecurityException("Source-matched native launcher/server absent");
            File lib = child(scratch,"runtime/lib/wine/arm64ec-windows");
            File boot = child(scratch,"runtime/lib/wine/arm64-windows/wineboot.exe");
            ByteArrayOutputStream blob = new ByteArrayOutputStream();
            try (InputStream input = context.getAssets().open(INDEX)) {
                byte[] block = new byte[4096]; int n;
                while ((n = input.read(block)) != -1) {
                    if (blob.size()+n > 65536)
                        throw new SecurityException("Wine28 index too large");
                    blob.write(block,0,n);
                }
            }
            JSONObject index = new JSONObject(blob.toString("UTF-8"));
            JSONArray modules = index.getJSONArray("module_files");
            if (modules.length() != COUNT || index.getInt("pe_count") != 23
                    || index.getInt("nls_count") != 76
                    || index.getInt("component_count") != 26
                    || index.getBoolean("launch_ready"))
                throw new SecurityException("Wine28 source index mismatch");
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
                } else throw new SecurityException("Unexpected Wine28 module");
                copyVerified(child(staged,name),dst,m.getLong("size"),m.getString("sha256"));
            }
            if (dll!=22 || exe!=1 || nls!=76 || !boot.isFile())
                throw new SecurityException("Wine28 verified scratch inventory incomplete");
            out.append("Fresh v7 scratch: 22 hybrid DLLs + ARM64 wineboot.exe + 76 NLS hashes PASS\n");
            File prefix=child(scratch,"prefix");
            mkdir(prefix);
            for (String p:new String[]{"home","tmp","cache","config","xdg-runtime"})
                mkdir(child(scratch,p));
            // The test is NOT wineboot -i: create only an empty private prefix.
            // A foreground server supplies a known-good socket before PE startup.
            serverLog=child(scratch,"v7-foreground-wineserver.log");
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
            out.append("V7 foreground wineserver socket observed: ").append(live[0]).append('\n');
            out.append("V7 foreground wineserver lock observed: ").append(live[1]).append('\n');
            out.append("V7 foreground server startup timeout: ").append(serverTimedOut).append('\n');
            out.append("V7 foreground server log cap exceeded: ").append(serverOverflow).append('\n');
            if (live[0]&&live[1]&&serverProc.isAlive()&&!serverOverflow) {
                peLog=child(scratch,"v7-wine-pe-help.log");
                ProcessBuilder p=new ProcessBuilder(loader.getAbsolutePath(),
                                                   boot.getAbsolutePath(),"--help");
                p.directory(scratch);
                p.redirectErrorStream(true);
                p.redirectOutput(peLog);
                cleanEnv(p,nativeDir,server,scratch,prefix,lib);
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
                out.append("Windows PE attempted: true (wineboot.exe --help ONLY; never -i)\n");
                out.append("PE process completed within 12s: ").append(finished).append('\n');
                out.append("PE exit code: ").append(finished?Integer.toString(exit):"BOUNDED STOP").append('\n');
                out.append("PE 12s deadline exceeded: ").append(expired).append('\n');
                out.append("PE log 2MiB cap exceeded: ").append(overflow).append('\n');
                out.append("Wineboot PE help marker observed: ").append(help).append('\n');
                out.append("Foreground server alive after PE process: ").append(serverProc.isAlive()).append('\n');
                out.append("PE loader output bounded:\n").append(peText).append('\n');
                if (finished&&exit==0&&help&&!expired&&!overflow)
                    out.append("RESULT: PASS — isolated Wine28 PE help reached; NOT Wineboot -i or Windows gaming\n");
                else
                    out.append("RESULT: FAIL — isolated Wine28 PE help did not complete; inspect preserved v7 logs\n");
            } else {
                out.append("Windows PE attempted: false — foreground server was not ready\n");
                out.append("RESULT: FAIL — v7 server handshake unavailable; no PE execution\n");
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
                out.append("Foreground v7 server terminated if running; no other prefix/server targeted\n");
                if (serverLog!=null)
                    out.append("V7 server debug log bounded:\n").append(boundedLog(serverLog)).append('\n');
            } catch (Exception e) {
                out.append("V7 cleanup/reading diagnostics: ")
                   .append(e.getClass().getSimpleName()).append('\n');
            }
        }
        out.append("V7 one-shot scratch retained; NEVER rerun/delete v7 after first use\n");
        out.append("v1-v6, Portal, user prefixes, original Wine and game saves: UNCHANGED\n");
        return out.toString();
    }
}
