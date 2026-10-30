package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
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
 * User-confirmed, one-shot Wine27 FIRST-PREFIX diagnostic only.
 * NEVER accesses any pre-existing prefix, rootfs, game, save or legacy cohort.
 * The only writable tree is a fresh noBackupFilesDir child; it is never erased
 * automatically, even after failure. A failed attempt requires diagnosis before
 * another generation may be authorized.
 */
public final class CharoiteWine27V4Trace {
    private static final String PACKAGE = "com.charoitx";
    private static final String STAGE_ROOT = "charoite-next-isolated-wine/wine10-arm64ec-bootstrap-0.6-staged";
    private static final String SCRATCH = "charoite-next-wine27-first-prefix-v4-trace";
    private static final String INDEX = "charoite-next/wine-bootstrap-27-index.json";
    private static final String NATIVE_LOADER = "libcharoite_wine27_loader.so";
    private static final String NATIVE_SERVER = "libcharoite_wine27_wineserver.so";
    private static final int COUNT = 99;
    private static final long LIMIT = 128L * 1024L * 1024L;
    private static final long TIMEOUT = 25L;
    private static final long MAX_LOG = 8L * 1024L * 1024L;
    private CharoiteWine27V4Trace() {}

    private static File child(File parent, String name) throws Exception {
        File base = parent.getCanonicalFile();
        File file = new File(base, name);
        if (!file.getCanonicalFile().toPath().startsWith(base.toPath())
                || file.getCanonicalFile().equals(base))
            throw new SecurityException("Wine27 path escapes isolated private directory");
        return file;
    }

    private static void mkdir(File dir) throws Exception {
        if ((!dir.exists() && !dir.mkdirs()) || !dir.isDirectory()
                || !dir.getCanonicalFile().equals(dir.getAbsoluteFile()))
            throw new SecurityException("Wine27 scratch directory is unsafe");
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
            throw new SecurityException("Unsafe staged Wine27 module");
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
                    throw new SecurityException("Wine27 copy exceeds source size");
                md.update(block, 0, n);
                output.write(block, 0, n);
            }
            output.getFD().sync();
        }
        if (count != size || !sha.equals(hex(md.digest())))
            throw new SecurityException("Wine27 scratch module source SHA mismatch");
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
        // Disable that secondary handoff only in this dedicated v4 trace.
        env.put("WINELOADERNOEXEC", "1");
        env.put("WINESERVER", server.getCanonicalPath());
        env.put("WINEDLLPATH", library.getCanonicalPath()
                + ":" + child(scratch,"runtime/lib/wine/arm64-windows").getCanonicalPath());
        env.put("CHAROITE_WINE27_NATIVE_DIR", nativeDir.getCanonicalPath());
        // Native Wine 10 ntdll and wineserver must use the new, verified
        // scratch-local NLS directory, never the read-only APK library tree.
        File dataDir = child(scratch,"runtime/share/wine");
        if (!child(dataDir,"nls/locale.nls").isFile()
                || !child(dataDir,"nls/l_intl.nls").isFile())
            throw new SecurityException("Fresh Wine27 NLS layout incomplete");
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

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — ISOLATED WINE27 V4 TRACED PREFIX BOOTSTRAP\n");
        out.append("One-shot opt-in: NEW v4 tracing scratch; v1/v2/v3 retained untouched\n");
        out.append("Wine22, games, saves, user prefixes, rootfs and v1/v2/v3 scratch: NOT ACCESSED\n");
        out.append("FEX, graphics, Steam, Battle.net, anti-cheat: NOT ATTEMPTED\n");
        out.append("A new Wine27 Wineboot and prefix MAY be created inside scratch ONLY\n\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return out.append("RESULT: BLOCKED — unsupported package/Android version\n").toString();

        // No filesystem mutation until BOTH previously device-verified gates
        // have been fully rechecked on this exact installed APK.
        String nativeGate = CharoiteWine27NativeGate.run(context);
        if (!nativeGate.contains("RESULT: PASS — matched Wine27 native --version gate; NOT runnable"))
            return out.append("RESULT: BLOCKED — staged data/native version gate failed\n")
                    .append(nativeGate).toString();
        out.append("Wine27 99 staged PE/NLS source hashes: PASS\n");
        out.append("Wine27 three native source hashes + version probes: PASS\n");
        File scratch = null;
        File prefix = null;
        File server = null;
        File loader = null;
        File nativeDir = null;
        boolean attempted = false;
        try {
            File privateBase = context.getNoBackupFilesDir().getCanonicalFile();
            File staged = child(privateBase,STAGE_ROOT);
            if (!staged.isDirectory()) throw new SecurityException("Wine27 staging absent");
            scratch = child(privateBase,SCRATCH);
            if (scratch.exists() || !scratch.mkdir())
                throw new SecurityException("One-shot Wine27 scratch already exists or unavailable; no overwrite");
            if (!scratch.getCanonicalFile().getParentFile().equals(privateBase))
                throw new SecurityException("Wine27 scratch parent changed");
            prefix = child(scratch,"prefix");
            if (prefix.exists())
                throw new SecurityException("Wine27 scratch prefix already exists");
            nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            loader = child(nativeDir,NATIVE_LOADER);
            server = child(nativeDir,NATIVE_SERVER);
            if (!loader.isFile() || !server.isFile())
                throw new SecurityException("Wine27 APK-native loader/server absent");

            // Reuse exactly the hash-verified stage files. No old Wine22 data,
            // external storage, app rootfs or existing user container is read.
            ByteArrayOutputStream blob = new ByteArrayOutputStream();
            try (InputStream source = context.getAssets().open(INDEX)) {
                byte[] block = new byte[2048]; int n;
                while ((n=source.read(block))!=-1) {
                    if (blob.size()+n > 65536)
                        throw new SecurityException("Wine27 index too large");
                    blob.write(block,0,n);
                }
            }
            JSONObject index = new JSONObject(blob.toString("UTF-8"));
            JSONArray modules = index.getJSONArray("module_files");
            if (modules.length() != COUNT || index.getInt("pe_count") != 23
                    || index.getInt("nls_count") != 76 || index.getInt("component_count")!=26
                    || index.getBoolean("launch_ready"))
                throw new SecurityException("Wine27 source inventory/readiness mismatch");
            File library = child(scratch,"runtime/lib/wine/arm64ec-windows");
            File boot = child(scratch,"runtime/lib/wine/arm64-windows/wineboot.exe");
            long total = 0;
            for (int i=0; i<modules.length(); i++)
                total += modules.getJSONObject(i).getLong("size");
            if (total<=0 || total>LIMIT || privateBase.getUsableSpace()<2*total+64L*1024*1024)
                throw new SecurityException("Insufficient safe Wine27 scratch capacity");
            int dll=0,nls=0,boots=0;
            for (int i=0; i<modules.length(); i++) {
                JSONObject module = modules.getJSONObject(i);
                String name=module.getString("path");
                File destination;
                if (name.matches("pe/arm64ec/[a-z0-9_]+\\.dll")) {
                    destination=child(library,name.substring("pe/arm64ec/".length()));
                    dll++;
                } else if (name.equals("pe/arm64/wineboot.exe")) {
                    destination=boot;
                    boots++;
                } else if (name.matches("nls/[a-z0-9_]+\\.nls")) {
                    destination=child(scratch,"runtime/share/wine/"+name);
                    nls++;
                } else throw new SecurityException("Untrusted Wine27 scratch layout path");
                File origin=child(staged,name);
                copyVerified(origin,destination,module.getLong("size"),module.getString("sha256"));
            }
            if (dll !=22 || nls!=76 || boots!=1 || !boot.isFile())
                throw new SecurityException("Wine27 scratch inventory incomplete");
            out.append("Scratch copy: 22 ARM64EC DLL + 1 ARM64 wineboot.exe + 76 NLS SHA-256 PASS\n");
            out.append("20 unbundled PE import names remain; not proven fatal\n");
            out.append("Native loader re-exec diagnostic: WINELOADERNOEXEC=1 (v4 only)\n");
            out.append("Native ntdll selection: CHAROITE_WINE27_NATIVE_DIR (source matched)\n");
            out.append("Native NLS selection: CHAROITE_WINE26_DATA_DIR (verified v4 scratch)\n");
            for (String dir:new String[]{"home","tmp","cache","config","xdg-runtime"})
                mkdir(child(scratch,dir));
            File log=child(scratch,"wineboot.log");
            Process process=null;
            int exit=-999;
            boolean finished=false;
            boolean logOverflow=false;
            boolean timeExpired=false;
            try {
                ProcessBuilder pb = new ProcessBuilder(loader.getAbsolutePath(),
                        boot.getAbsolutePath(),"-i");
                pb.directory(scratch);
                pb.redirectErrorStream(true);
                pb.redirectOutput(log);
                cleanEnv(pb,nativeDir,server,scratch,prefix,library);
                attempted=true;
                process=pb.start();
                // 8 MiB on-disk trace cap, even if native Wine becomes noisy.
                // No trace is emitted to the Android UI until the process exits.
                long start = System.nanoTime();
                while (!finished && !logOverflow && !timeExpired) {
                    finished=process.waitFor(200,TimeUnit.MILLISECONDS);
                    if (finished) exit=process.exitValue();
                    else if (log.length()>MAX_LOG) logOverflow=true;
                    else if (System.nanoTime()-start >= TimeUnit.SECONDS.toNanos(TIMEOUT))
                        timeExpired=true;
                }
                if (!finished) {
                    process.destroyForcibly();
                    process.waitFor(3,TimeUnit.SECONDS);
                }
            } finally {
                if (process!=null && process.isAlive()) process.destroyForcibly();
                // Scoped strictly to this NEW WINEPREFIX, never a user prefix.
                // Do not delete any diagnostic scratch files or registry.
                if (attempted) {
                    try {
                        ProcessBuilder stop=new ProcessBuilder(server.getAbsolutePath(),"-k");
                        cleanEnv(stop,nativeDir,server,scratch,prefix,library);
                        stop.redirectErrorStream(true);
                        stop.redirectOutput(child(scratch,"wineserver-stop.log"));
                        Process stopper=stop.start();
                        if (!stopper.waitFor(5,TimeUnit.SECONDS)) {
                            stopper.destroyForcibly();
                            stopper.waitFor(2,TimeUnit.SECONDS);
                        }
                        out.append("Isolated-prefix wineserver stop requested\n");
                    } catch (Exception stopError) {
                        out.append("Isolated wineserver stop: ")
                           .append(stopError.getClass().getSimpleName()).append("\n");
                    }
                }
            }
            out.append("Wineboot command: APK native Wine27 loader + staged ARM64 wineboot.exe -i\n");
            out.append("Earlier failed Wine v1/v2/v3 scratches: NOT ACCESSED\n");
            out.append("V4 trace channels: err+all, loaddll, module, process, seh, server\n");
            out.append("V4 log-size cap 8 MiB exceeded: ").append(logOverflow).append('\n');
            out.append("V4 25s process deadline exceeded: ").append(timeExpired).append('\n');
            out.append("Wineboot completed within 25s: ").append(finished).append('\n');
            out.append("Wineboot exit code: ").append(finished?Integer.toString(exit):"TIMEOUT").append('\n');
            out.append("New private prefix directory created: ").append(prefix.isDirectory()).append('\n');
            out.append("New private user.reg: ").append(child(prefix,"user.reg").isFile()).append('\n');
            out.append("New private system.reg: ").append(child(prefix,"system.reg").isFile()).append('\n');
            out.append("Diagnostic output (bounded):\n").append(boundedLog(log)).append('\n');
            if (finished && !logOverflow && !timeExpired && exit==0 && child(prefix,"system.reg").isFile()
                    && child(prefix,"user.reg").isFile())
                out.append("RESULT: PASS — fresh isolated v4 Wine27 prefix bootstrapped; games NOT ready\n");
            else
                out.append("RESULT: FAIL — isolated v4 traced bootstrap not yet verified\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName())
                    .append(": ").append(error.getMessage()).append('\n');
        }
        out.append("Disposable probe data retained for inspection; NEVER auto-deleted\n");
        out.append("Existing Wine22, Portal data, games and saves: UNCHANGED\n");
        return out.toString();
    }
}
