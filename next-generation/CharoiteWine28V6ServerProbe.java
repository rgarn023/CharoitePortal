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
import java.io.RandomAccessFile;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Opt-in, one-shot, SERVER-ONLY smoke test in a new private v6 scratch.
 * No Wine loader, PE, Wineboot, existing prefix or prior v1-v5 scratch is
 * opened. This does not install/validate a Windows runtime.
 */
public final class CharoiteWine28V6ServerProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine28-server-only-v6";
    private static final String STAGE = "charoite-next-isolated-wine/wine10-arm64ec-bootstrap-0.7-staged";
    private static final String INDEX = "charoite-next/wine-bootstrap-28-index.json";
    private static final String SERVER = "libcharoite_wine28_wineserver.so";
    private static final long DEADLINE_SECONDS = 8L;
    private static final long LOG_CAP = 256L * 1024L;
    private CharoiteWine28V6ServerProbe() {}

    private static File checked(File root, String relative) throws Exception {
        File base = root.getCanonicalFile();
        File file = new File(base, relative);
        if (!file.getCanonicalFile().toPath().startsWith(base.toPath())
                || file.getCanonicalFile().equals(base)
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("New v6 scratch path is unsafe");
        return file;
    }
    private static void mkdir(File dir) throws Exception {
        if ((!dir.exists() && !dir.mkdirs()) || !dir.isDirectory()
                || !dir.getCanonicalFile().equals(dir.getAbsoluteFile()))
            throw new SecurityException("Could not create new v6-only directory");
    }
    private static String hex(byte[] bytes) {
        StringBuilder text = new StringBuilder();
        for (byte value : bytes) text.append(String.format(Locale.US, "%02x", value & 255));
        return text.toString();
    }
    private static void copyNls(File source, File target, long size, String sha)
            throws Exception {
        if (!source.isFile() || !source.getCanonicalFile().equals(source.getAbsoluteFile())
                || target.exists() || size < 1 || size > 4L * 1024 * 1024
                || source.length() != size || !sha.matches("[a-f0-9]{64}"))
            throw new SecurityException("Unsafe verified Wine28 NLS source");
        mkdir(target.getParentFile());
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long total = 0;
        try (InputStream input = new FileInputStream(source);
             FileOutputStream output = new FileOutputStream(target)) {
            byte[] block = new byte[8192];
            int n;
            while ((n = input.read(block)) != -1) {
                total += n;
                if (total > size) throw new SecurityException("NLS size changed");
                digest.update(block, 0, n);
                output.write(block, 0, n);
            }
            output.getFD().sync();
        }
        if (total != size || !sha.equals(hex(digest.digest())))
            throw new SecurityException("NLS copied hash mismatch");
    }
    private static boolean[] socketAndLock(File prefix) throws Exception {
        boolean socket = false, lock = false;
        File top = checked(prefix, ".wineserver");
        if (!top.isDirectory()) return new boolean[]{false, false};
        File[] entries = top.listFiles();
        if (entries == null) return new boolean[]{false, false};
        int inspected = 0;
        for (File item : entries) {
            if (inspected++ >= 16) break;
            if (!item.getName().matches("server-[0-9a-f]+-[0-9a-f]+")
                    || !item.getCanonicalFile().equals(item.getAbsoluteFile())
                    || !item.isDirectory()) continue;
            for (String name : new String[]{"socket", "lock"}) {
                File candidate = checked(item, name);
                try {
                    StructStat info = Os.lstat(candidate.getAbsolutePath());
                    if (name.equals("socket") && OsConstants.S_ISSOCK(info.st_mode)) socket = true;
                    if (name.equals("lock") && OsConstants.S_ISREG(info.st_mode)) lock = true;
                } catch (android.system.ErrnoException absent) {
                    // A missing socket or lock remains false; do not follow links.
                }
            }
        }
        return new boolean[]{socket, lock};
    }
    private static String boundedLog(File file) throws Exception {
        if (!file.isFile()) return "(no output)";
        long size = file.length();
        if (size == 0) return "(empty)";
        try (RandomAccessFile f = new RandomAccessFile(file, "r")) {
            int n = (int)Math.min(size, 12000L);
            byte[] bytes = new byte[n];
            f.readFully(bytes);
            String head = new String(bytes, "UTF-8");
            if (size > n) head += "\n[... further bytes omitted; total " + size + " ...]";
            return head;
        }
    }

    public static String run(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — NEW ISOLATED WINE28 V6 WINESERVER-ONLY SMOKE\n");
        report.append("Explicit one-shot consent; NO Wineboot, Windows PE or FEX/graphics execution\n");
        report.append("Wine22, stable Portal, games, saves, user prefixes, v1/v2/v3/v4/v5: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return report.append("RESULT: BLOCKED — wrong package or Android version\n").toString();

        // Source SHA and version-only native ELF gate; this never reads old user data.
        String gate = CharoiteWine28NativeGate.run(context);
        if (!gate.contains("RESULT: PASS — matched Wine28 native --version gate; NOT runnable"))
            return report.append("RESULT: BLOCKED — Wine28 native/source gate not verified\n")
                    .append(gate).toString();
        report.append("Wine28 99 PE/NLS and three native hashes + version-only checks: PASS\n");

        File scratch = null;
        Process process = null;
        try {
            File base = context.getNoBackupFilesDir().getCanonicalFile();
            File staged = checked(base, STAGE);
            if (!staged.isDirectory())
                throw new SecurityException("Wine28 0.7 staged data missing");
            scratch = checked(base, SCRATCH);
            if (scratch.exists() || !scratch.mkdir())
                throw new SecurityException("V6 already used or unavailable; NEVER overwrite");
            if (!scratch.getCanonicalFile().getParentFile().equals(base))
                throw new SecurityException("V6 scratch parent changed");
            File prefix = checked(scratch, "prefix");
            mkdir(prefix);
            for (String path : new String[]{"home", "tmp", "cache", "xdg-runtime"})
                mkdir(checked(scratch, path));

            ByteArrayOutputStream raw = new ByteArrayOutputStream();
            try (InputStream input = context.getAssets().open(INDEX)) {
                byte[] block = new byte[4096];
                int n;
                while ((n = input.read(block)) != -1) {
                    if (raw.size() + n > 65536)
                        throw new SecurityException("Wine28 index too large");
                    raw.write(block, 0, n);
                }
            }
            JSONArray files = new JSONObject(raw.toString("UTF-8")).getJSONArray("module_files");
            if (files.length() != 99)
                throw new SecurityException("Unexpected Wine28 source inventory");
            int nlsCopied = 0;
            for (int i = 0; i < files.length(); i++) {
                JSONObject part = files.getJSONObject(i);
                String path = part.getString("path");
                if (!path.equals("nls/locale.nls") && !path.equals("nls/l_intl.nls"))
                    continue;
                copyNls(checked(staged, path),
                        checked(scratch, "runtime/share/wine/" + path),
                        part.getLong("size"), part.getString("sha256"));
                nlsCopied++;
            }
            if (nlsCopied != 2)
                throw new SecurityException("Required server NLS entries absent");
            report.append("New v6 NLS copy: 2/2 source SHA-256 PASS\n");

            File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            File server = checked(nativeDir, SERVER);
            if (!server.isFile()) throw new SecurityException("Source-matched wineserver not installed");
            File log = checked(scratch, "wineserver-v6.log");
            ProcessBuilder pb = new ProcessBuilder(server.getAbsolutePath(), "-f", "-d");
            pb.directory(scratch);
            pb.redirectErrorStream(true);
            pb.redirectOutput(log);
            Map<String,String> env = pb.environment();
            env.clear();
            env.put("PATH", "/system/bin:/system/xbin");
            env.put("HOME", checked(scratch, "home").getCanonicalPath());
            env.put("TMPDIR", checked(scratch, "tmp").getCanonicalPath());
            env.put("XDG_RUNTIME_DIR", checked(scratch, "xdg-runtime").getCanonicalPath());
            env.put("XDG_CACHE_HOME", checked(scratch, "cache").getCanonicalPath());
            env.put("WINEPREFIX", prefix.getCanonicalPath());
            env.put("CHAROITE_WINE26_DATA_DIR",
                    checked(scratch, "runtime/share/wine").getCanonicalPath());
            env.put("LC_ALL", "C");
            // -f forbids daemonization; -d enables bounded native server diagnostics.
            process = pb.start();
            long start = System.nanoTime();
            boolean finished = false, overflow = false, limit = false;
            boolean socketObserved = false, lockObserved = false;
            int exit = -999;
            while (!finished && !overflow && !limit) {
                finished = process.waitFor(200, TimeUnit.MILLISECONDS);
                boolean[] observed = socketAndLock(prefix);
                socketObserved |= observed[0];
                lockObserved |= observed[1];
                if (finished) exit = process.exitValue();
                overflow = log.length() > LOG_CAP;
                limit = System.nanoTime() - start >= TimeUnit.SECONDS.toNanos(DEADLINE_SECONDS);
            }
            if (process.isAlive()) {
                process.destroyForcibly();
                process.waitFor(3, TimeUnit.SECONDS);
            }
            report.append("V6 command: APK matched wineserver -f -d (foreground only)\n");
            report.append("Wineserver exited naturally: ").append(finished).append('\n');
            report.append("Wineserver exit: ").append(finished ? Integer.toString(exit) : "BOUNDED STOP").append('\n');
            report.append("8s deadline reached: ").append(limit).append('\n');
            report.append("256KiB output cap exceeded: ").append(overflow).append('\n');
            report.append("V6 server lock observed: ").append(lockObserved).append('\n');
            report.append("V6 live Unix socket observed: ").append(socketObserved).append('\n');
            report.append("V6 native stderr/stdout (bounded):\n").append(boundedLog(log)).append('\n');
            if (socketObserved && lockObserved && !overflow && (!finished || exit == 0))
                report.append("RESULT: PASS — isolated native server socket observed; NO Wineboot or PE capability established\n");
            else
                report.append("RESULT: FAIL — isolated native wineserver startup not established\n");
        } catch (Exception ex) {
            report.append("RESULT: BLOCKED — ")
                .append(ex.getClass().getSimpleName()).append(": ")
                .append(ex.getMessage()).append('\n');
        } finally {
            if (process != null && process.isAlive()) process.destroyForcibly();
        }
        report.append("V6 scratch/log kept unchanged for inspection; NEVER retry if v6 exists\n");
        report.append("v1-v5, Portal, rootfs, original Wine, games and saves: UNCHANGED\n");
        return report.toString();
    }
}
