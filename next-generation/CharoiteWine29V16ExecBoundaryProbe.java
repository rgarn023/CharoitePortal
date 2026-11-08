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
 * Explicit opt-in, one-shot V16 native exec boundary diagnostic.
 * Preserves V15's Windows C: path and scoped NOEXEC=1 without reusing V15.
 * A brand-new V16 private prefix only; Wineboot and internal helpers may run.
 * The sc.exe command has a Windows path only, no service arguments or SCM query; no games.
 * Previous V14 and older scratch, user prefixes, games, saves, rootfs and stable Portal
 * are never accessed. The V16 scratch is retained and never retried or deleted.
 */
public final class CharoiteWine29V16ExecBoundaryProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String STAGE_ROOT = "charoite-next-wine29-012-sealed-pe-nls/wine10-arm64ec-dependencies-0.12-sealed-pe-nls";
    private static final String SCRATCH = "charoite-next-wine29-entry-v16";
    private static final String INDEX = "charoite-next/wine29-sealed012/wine29-sealed012-index.json";
    private static final String NATIVE_LOADER = "libcharoite_wine29_v6_loader.so";
    private static final String NATIVE_SERVER = "libcharoite_wine29_v6_wineserver.so";
    private static final String V6_INDEX = "charoite-next/wine29-v6/wine29-v6-native-index.json";
    private static final String V6_NTDLL = "libcharoite_wine29_v6_ntdll.so";
    private static final String SERVICES_INDEX = "charoite-next/wine29-v7-services/services-index.json";
    private static final String SERVICES_ASSET = "charoite-next/wine29-v7-services/services-arm64.exe.bin";
    private static final String USERENV_INDEX = "charoite-next/wine29-v8-userenv/userenv-index.json";
    private static final String USERENV_ASSET = "charoite-next/wine29-v8-userenv/userenv-arm64.dll.bin";
    private static final String SC_INDEX = "charoite-next/wine29-v9-sc/sc-index.json";
    private static final String SC_ASSET = "charoite-next/wine29-v9-sc/sc-arm64.exe.bin";
    private static final int COUNT = 111;
    private static final long LIMIT = 128L * 1024L * 1024L;
    private static final long TIMEOUT = 25L;
    private static final long MAX_LOG = 8L * 1024L * 1024L;
    private CharoiteWine29V16ExecBoundaryProbe() {}

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

    /**
     * Reproduce Wine 10's default initial C: mapping ONLY in fresh v16 scratch.
     * Native Wine normally creates drive_c and dosdevices/c: when it creates
     * dosdevices; if dosdevices was already created, the native routine skips
     * that block. This never visits an old prefix, never removes any file,
     * never creates Windows/Users/Program Files (those are Wine's work).
     */
    private static File prepareFreshDriveC(File prefix) throws Exception {
        File disk = child(prefix,"drive_c");
        File dos = child(prefix,"dosdevices");
        if (disk.exists() || dos.exists())
            throw new SecurityException("V16 C: preseed must start with no existing drive mapping");
        mkdir(disk);
        mkdir(dos);
        File link = child(dos,"c:");
        if (link.exists() || !disk.getCanonicalFile().equals(disk.getAbsoluteFile()))
            throw new SecurityException("V6 C: drive directory or link is unsafe");
        // A relative link cannot point outside this new prefix.
        Os.symlink("../drive_c",link.getAbsolutePath());
        StructStat stat = Os.lstat(link.getAbsolutePath());
        if (!OsConstants.S_ISLNK(stat.st_mode)
                || !"../drive_c".equals(Os.readlink(link.getAbsolutePath()))
                || !link.getCanonicalFile().equals(disk.getCanonicalFile()))
            throw new SecurityException("V6 C: mapping is not exact isolated relative symlink");
        return link;
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
        // Skip only Wine initial pre-exec; later Wine child-process exec still happens.
        // The source-patched v6 NTDLL redirects that child to the verified APK path.
        env.put("WINELOADERNOEXEC", "1");
        env.put("WINESERVER", server.getCanonicalPath());
        // Wine's ARM64 get_pe_dir() appends /aarch64-windows to each search ROOT.
        // Previous v7 mistakenly supplied a directory of PE DLLs directly.
        // The v16 scratch uses the correct root and directory layout.
        env.put("WINEDLLPATH", child(scratch,"runtime/lib/wine").getCanonicalPath());
        env.put("CHAROITE_WINE29_V6_NATIVE_DIR", nativeDir.getCanonicalPath());
        File childLoader = child(nativeDir, NATIVE_LOADER);
        if (!childLoader.isFile() || !childLoader.getCanonicalFile().equals(childLoader.getAbsoluteFile()))
            throw new SecurityException("V6 source-verified child loader absent from nativeLibraryDir");
        env.put("CHAROITE_WINE29_V6_LOADER_EXEC", childLoader.getCanonicalPath());
        // Initial PE NTDLL lookup, before ordinary WINEDLLPATH DLL resolution.
        // The 111 PE/NLS files were copied with SHA-256 verification in v6 only.
        File peNtdll = child(library,"ntdll.dll");
        if (!peNtdll.isFile()
                || !peNtdll.getCanonicalFile().equals(peNtdll.getAbsoluteFile()))
            throw new SecurityException("Wine29 verified Windows NTDLL PE absent");
        env.put("CHAROITE_WINE29_V6_PE_DIR", library.getCanonicalPath());
        // Native Wine 10 ntdll and wineserver must use the new, verified
        // scratch-local NLS directory, never the read-only APK library tree.
        File dataDir = child(scratch,"runtime/share/wine");
        if (!child(dataDir,"nls/locale.nls").isFile()
                || !child(dataDir,"nls/l_intl.nls").isFile())
            throw new SecurityException("Fresh Wine29 NLS layout incomplete");
        env.put("CHAROITE_WINE29_V6_DATA_DIR", dataDir.getCanonicalPath());
        env.put("LC_ALL", "C");
        return env;
    }

    private static String sanitizeLog(String value, File root) {
        StringBuilder safe = new StringBuilder();
        String prefix = root.getAbsolutePath();
        for (String line : value.split("\n", -1)) {
            String lower = line.toLowerCase(Locale.US);
            if (lower.contains("env=") || lower.contains("password")
                    || lower.contains("secret") || lower.contains("token=")) {
                safe.append("[redacted sensitive process line]\n");
                continue;
            }
            String cleaned = line.replace(prefix, "[v6-private-scratch]")
                    .replace('\r', ' ').replace('\0', ' ');
            safe.append(cleaned.length() > 760 ? cleaned.substring(0, 760) + " [clipped]" : cleaned).append('\n');
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

    /** Verify v6 APK-owned native ELF cohort BEFORE a private scratch exists. */
    private static void verifyV6Native(Context context) throws Exception {
        if (!PACKAGE.equals(context.getPackageName()))
            throw new SecurityException("Only experimental Next app may run v6");
        ByteArrayOutputStream raw = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(V6_INDEX)) {
            byte[] block = new byte[4096];
            int n;
            while ((n = input.read(block)) != -1) {
                if (raw.size() + n > 8192)
                    throw new SecurityException("Oversized v6 native sealed index");
                raw.write(block, 0, n);
            }
        }
        JSONObject index = new JSONObject(raw.toString("UTF-8"));
        if (index.getInt("schema_version") != 1
                || !PACKAGE.equals(index.getString("package"))
                || !index.getBoolean("preflight_verified")
                || !index.getBoolean("apk_only_native_stage")
                || index.getBoolean("launch_ready")
                || index.getBoolean("native_executed")
                || index.getBoolean("wineboot_executed")
                || index.getBoolean("prefix_created")
                || index.getBoolean("device_tested")
                || index.getBoolean("games_tested")
                || !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(index.getString("native_source_revision"))
                || !"wine10-arm64ec-dependencies.0.12-sealed-data-candidate".equals(index.getString("sealed_111_file_cohort")))
            throw new SecurityException("V6 native APK source or readiness manifest incorrect");
        JSONObject files = index.getJSONObject("native_files");
        if (files.length() != 3)
            throw new SecurityException("V6 native cohort is not exactly three files");
        File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
        if (!nativeDir.isDirectory() || !nativeDir.getAbsolutePath().contains("/lib/arm64"))
            throw new SecurityException("V6 native cohort not in APK-owned ARM64 library directory");
        for (String key : new String[]{"loader", "ntdll", "wineserver"}) {
            String filename = "libcharoite_wine29_v6_" + key + ".so";
            JSONObject rec = files.getJSONObject(key);
            long size = rec.getLong("size");
            if (!filename.equals(rec.getString("filename"))
                    || !"AArch64".equals(rec.getString("elf_machine"))
                    || rec.getLong("min_load_alignment") < 16384L
                    || size < 1024L || size > 32L*1024L*1024L
                    || !rec.getString("sha256").matches("[0-9a-f]{64}"))
                throw new SecurityException("V6 APK native manifest rejects " + key);
            File file = child(nativeDir,filename);
            StructStat stat = Os.lstat(file.getAbsolutePath());
            if (!OsConstants.S_ISREG(stat.st_mode)
                    || file.length()!=size || !file.canExecute()
                    || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
                throw new SecurityException("V6 APK native ELF unsafe: " + key);
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            long count=0;
            try (InputStream in = new FileInputStream(file)) {
                int n; byte[] buf = new byte[16384];
                while ((n=in.read(buf))!=-1) {
                    count += n;
                    if (count > size) throw new SecurityException("V6 native ELF oversized");
                    md.update(buf,0,n);
                }
            }
            if (count != size || !rec.getString("sha256").equals(hex(md.digest())))
                throw new SecurityException("V6 native ELF hash mismatch: " + key);
        }
    }


    /** Inspect and SHA-256-verify the source-built ARM64 services.exe APK asset
     * BEFORE creating a new scratch or launching anything. The historical v6
     * scratch is neither visited nor used. */
    private static byte[] verifyV7Services(Context context) throws Exception {
        ByteArrayOutputStream indexBytes = new ByteArrayOutputStream();
        try (InputStream src = context.getAssets().open(SERVICES_INDEX)) {
            byte[] buf=new byte[4096]; int n;
            while ((n=src.read(buf))!=-1) {
                if (indexBytes.size()+n>8192) throw new SecurityException("V7 source index oversized");
                indexBytes.write(buf,0,n);
            }
        }
        JSONObject index = new JSONObject(indexBytes.toString("UTF-8"));
        if (index.getInt("schema_version")!=1 || !PACKAGE.equals(index.getString("package"))
                || !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(index.getString("wine_source_commit"))
                || index.getLong("source_run")!=42409561051L
                || !"f32a3563254b2ae6447d6cf2e6639be3e7e6d9d9".equals(index.getString("source_build_commit"))
                || index.getLong("source_artifact_id")!=13589325323L
                || !"sha256:fba183ee44a632c2e45608dace22ce71108129882e2854fd51bf077c04247a34".equals(index.getString("source_artifact_digest"))
                || !"services.exe".equals(index.getString("image_name"))
                || !"0xAA64".equals(index.getString("pe_machine"))
                || !SERVICES_ASSET.equals(index.getString("asset"))
                || !index.getBoolean("apk_stage_only")
                || index.getBoolean("windows_executed")
                || index.getBoolean("prefix_initialized")
                || index.getBoolean("launch_ready")
                || index.getJSONArray("ordinary_imports").length()!=7
                || index.getJSONArray("delay_imports").length()!=0)
            throw new SecurityException("V7 services.exe source integrity metadata mismatch");
        long expectedSize=index.getLong("size");
        String expectedHash=index.getString("sha256");
        if (expectedSize<1024 || expectedSize>16L*1024L*1024L || !expectedHash.matches("[a-f0-9]{64}"))
            throw new SecurityException("V7 services.exe index size/hash unsafe");
        ByteArrayOutputStream data=new ByteArrayOutputStream((int)expectedSize);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream src=context.getAssets().open(SERVICES_ASSET)) {
            byte[] buf=new byte[16384]; int n;
            while ((n=src.read(buf))!=-1) {
                if (data.size()+n>expectedSize)
                    throw new SecurityException("V7 services.exe asset oversized");
                digest.update(buf,0,n);
                data.write(buf,0,n);
            }
        }
        byte[] pe=data.toByteArray();
        if (pe.length!=expectedSize || !expectedHash.equals(hex(digest.digest())))
            throw new SecurityException("V7 services.exe packaged PE SHA-256 mismatch");
        int offset=(pe[0x3c]&255)|((pe[0x3d]&255)<<8)|((pe[0x3e]&255)<<16)|((pe[0x3f]&255)<<24);
        if (pe.length<128 || pe[0]!='M' || pe[1]!='Z'
                || offset<64 || offset>pe.length-24
                || pe[offset]!='P' || pe[offset+1]!='E'
                || pe[offset+2]!=0 || pe[offset+3]!=0
                || (pe[offset+4]&255)!=0x64 || (pe[offset+5]&255)!=0xaa)
            throw new SecurityException("V7 services.exe is not Windows ARM64 PE AA64");
        return pe;
    }

    private static byte[] verifyV8Userenv(Context context) throws Exception {
        ByteArrayOutputStream indexBytes = new ByteArrayOutputStream();
        try (InputStream src = context.getAssets().open(USERENV_INDEX)) {
            byte[] buf=new byte[4096]; int n;
            while ((n=src.read(buf))!=-1) {
                if (indexBytes.size()+n>8192) throw new SecurityException("V8 source index oversized");
                indexBytes.write(buf,0,n);
            }
        }
        JSONObject index = new JSONObject(indexBytes.toString("UTF-8"));
        if (index.getInt("schema_version")!=1 || !PACKAGE.equals(index.getString("package"))
                || !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(index.getString("wine_source_commit"))
                || index.getLong("source_run")!=42419386776L
                || !"523e66511a3504f0705eee508c0fc935999dca2f".equals(index.getString("source_build_commit"))
                || index.getLong("source_artifact_id")!=13593275372L
                || !"sha256:524ed4e41b418095c8cb546e31f0754522ce6c3b8501c643feea826c661fc887".equals(index.getString("source_artifact_digest"))
                || !"userenv.dll".equals(index.getString("image_name"))
                || !"0xAA64".equals(index.getString("pe_machine"))
                || !USERENV_ASSET.equals(index.getString("asset"))
                || !index.getBoolean("apk_stage_only")
                || index.getBoolean("windows_executed")
                || index.getBoolean("prefix_initialized")
                || index.getBoolean("launch_ready")
                || (index.getJSONArray("ordinary_imports").length()<1 || index.getJSONArray("ordinary_imports").length()>12)
                || index.getJSONArray("delay_imports").length()!=0
                || index.getJSONArray("ordinary_imports_unbundled_after_candidate").length()!=0
                || index.getJSONArray("all_unbundled_after_candidate").length()!=0
                || !"0xA64E".equals(index.getString("arm64x_container_machine")))
            throw new SecurityException("V8 userenv.dll source integrity metadata mismatch");
        long expectedSize=index.getLong("size");
        String expectedHash=index.getString("sha256");
        if (expectedSize<1024 || expectedSize>16L*1024L*1024L || !expectedHash.matches("[a-f0-9]{64}"))
            throw new SecurityException("V8 userenv.dll index size/hash unsafe");
        ByteArrayOutputStream data=new ByteArrayOutputStream((int)expectedSize);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream src=context.getAssets().open(USERENV_ASSET)) {
            byte[] buf=new byte[16384]; int n;
            while ((n=src.read(buf))!=-1) {
                if (data.size()+n>expectedSize)
                    throw new SecurityException("V8 userenv.dll asset oversized");
                digest.update(buf,0,n);
                data.write(buf,0,n);
            }
        }
        byte[] pe=data.toByteArray();
        if (pe.length!=expectedSize || !expectedHash.equals(hex(digest.digest())))
            throw new SecurityException("V8 userenv.dll packaged PE SHA-256 mismatch");
        int offset=(pe[0x3c]&255)|((pe[0x3d]&255)<<8)|((pe[0x3e]&255)<<16)|((pe[0x3f]&255)<<24);
        if (pe.length<128 || pe[0]!='M' || pe[1]!='Z'
                || offset<64 || offset>pe.length-24
                || pe[offset]!='P' || pe[offset+1]!='E'
                || pe[offset+2]!=0 || pe[offset+3]!=0
                || (pe[offset+4]&255)!=0x64 || (pe[offset+5]&255)!=0xaa)
            throw new SecurityException("V8 userenv.dll is not Windows ARM64 PE AA64");
        return pe;
    }


    /** Fail closed on all pinned v9 sc.exe evidence BEFORE any new scratch exists. */
    private static byte[] verifyV16Sc(Context context) throws Exception {
        ByteArrayOutputStream rawIndex = new ByteArrayOutputStream();
        try (InputStream input=context.getAssets().open(SC_INDEX)) {
            int n; byte[] buf=new byte[4096];
            while ((n=input.read(buf))!=-1) {
                if (rawIndex.size()+n>8192) throw new SecurityException("V16 SCM index oversized");
                rawIndex.write(buf,0,n);
            }
        }
        JSONObject index=new JSONObject(rawIndex.toString("UTF-8"));
        if (index.getInt("schema_version")!=1
                || !PACKAGE.equals(index.getString("package"))
                || !"c74acb09d51b447f5d5ac56c87608d3ec565a767".equals(index.getString("wine_source_commit"))
                || index.getLong("source_run")!=42426173638L
                || !"311a141fa255886020c5e2adab643db0e954a07a".equals(index.getString("source_build_commit"))
                || index.getLong("source_artifact_id")!=13595845868L
                || !"sha256:f8ac4ddbdca513a07ee15b29101b78203d07cd9094e65357e50b9709887e6c54".equals(index.getString("source_artifact_digest"))
                || !"sc.exe".equals(index.getString("image_name"))
                || !"0xAA64".equals(index.getString("pe_machine"))
                || !SC_ASSET.equals(index.getString("asset"))
                || !index.getBoolean("apk_stage_only")
                || index.getBoolean("windows_executed")
                || index.getBoolean("device_tested")
                || index.getBoolean("prefix_initialized")
                || index.getBoolean("scm_verified")
                || index.getBoolean("launch_ready")
                || !index.getBoolean("previous_sealed_111_unchanged")
                || !index.getBoolean("prior_v6_native_cohort_unchanged")
                || !index.getBoolean("prior_v7_services_unchanged")
                || !index.getBoolean("prior_v8_userenv_unchanged")
                || index.getJSONArray("unbundled_imports").length()!=0
                || index.getJSONArray("delay_imports").length()!=0) {
            throw new SecurityException("V16 pinned ARM64 sc.exe source or ancestry mismatch");
        }
        JSONArray imports=index.getJSONArray("ordinary_imports");
        boolean advapi=false;
        for(int i=0;i<imports.length();i++)
            if ("advapi32.dll".equals(imports.getString(i))) advapi=true;
        if (!advapi || imports.length()>8) throw new SecurityException("V16 SCM PE imports invalid");
        long length=index.getLong("size");
        String hash=index.getString("sha256");
        if (length<1024 || length>16L*1024*1024 || !hash.matches("[a-f0-9]{64}"))
            throw new SecurityException("V16 SCM PE asset index size/hash unsafe");
        ByteArrayOutputStream data=new ByteArrayOutputStream((int)length);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream input=context.getAssets().open(SC_ASSET)) {
            int n;byte[] buf=new byte[16384];
            while((n=input.read(buf))!=-1) {
                if (data.size()+n>length) throw new SecurityException("V16 SCM PE asset too large");
                data.write(buf,0,n);digest.update(buf,0,n);
            }
        }
        byte[] pe=data.toByteArray();
        if (pe.length!=length || !hash.equals(hex(digest.digest())) || pe.length<128
                || pe[0]!='M' || pe[1]!='Z')
            throw new SecurityException("V16 SCM asset SHA-256/DOS header failed");
        int offset=(pe[0x3c]&255)|((pe[0x3d]&255)<<8)|((pe[0x3e]&255)<<16)|((pe[0x3f]&255)<<24);
        if(offset<64 || offset>pe.length-24 || pe[offset]!='P' || pe[offset+1]!='E'
                || pe[offset+2]!=0 || pe[offset+3]!=0
                || (pe[offset+4]&255)!=0x64 || (pe[offset+5]&255)!=0xaa)
            throw new SecurityException("V16 SCM client not ARM64 PE AA64");
        return pe;
    }

    private static String shortReport(StringBuilder report) {
        final String tail="\nEND OF SHORT V16 ENTRY REPORT — V16 evidence preserved if generated; all previous generations untouched.\n";
        final int limit=9000-tail.length();
        String summary=report.toString();
        if(summary.length()>limit)
            summary=summary.substring(0,limit-100)+"\n[Clipped to 9,000 characters; log evidence retained.]\n";
        return summary+tail;
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder("Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md\n");
        out.append("CHAROITE NEXT — ISOLATED WINE29 V16 INDEPENDENT SC.EXE NATIVE EXEC-BOUNDARY DIAGNOSTIC\n");
        out.append("EXPLICIT ONE-SHOT OPT-IN; NEW private v16 prefix ONLY; Wineboot/services.exe/sc.exe MAY execute; NO games\n");
        out.append("Source-verified v9 sc.exe, v8 userenv.dll, v7 services.exe and original native/sealed modules, NEW v16 scratch ONLY\n");
        out.append("Wine28, prior Wine29 v1-v15 scratch, stable Portal, games/saves/user prefixes/rootfs: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return shortReport(out.append("RESULT: BLOCKED — unsupported package/device\n"));
        String preflight = CharoiteWine29Sealed012PePreflight.run(context);
        if (!preflight.contains("RESULT: PASS — isolated Wine29 0.12 34-DLL direct/delay PE preflight; NOT RUNNABLE"))
            return shortReport(out.append("RESULT: BLOCKED — sealed Wine29 34-DLL PE import preflight failed; NO new scratch\n")
                .append(preflight));
        out.append("Wine29 34-DLL header/ordinary/delay import preflight: PASS\n");
        String gate = CharoiteWine29Sealed012Stage.verifyOnly(context);
        if (!gate.contains("RESULT: PASS — isolated Wine29 0.12 data-only stage; NOT RUNNABLE"))
            return shortReport(out.append("RESULT: BLOCKED — matched Wine29 111-file source/PE/NLS/native SHA-256 gate failed\n")
                .append(gate));
        out.append("Wine29 staged 111 PE/NLS and APK-native three ELF hashes: PASS\n");

        byte[] servicesImage;
        byte[] userenvImage;
        byte[] scImage;
        try {
            verifyV6Native(context);
            servicesImage=verifyV7Services(context);
            userenvImage=verifyV8Userenv(context);
            scImage=verifyV16Sc(context);
            out.append("V16 ARM64 sc.exe source SHA-256/import/PE gate: PASS\n");
            out.append("V8 source-built ARM64X userenv.dll APK SHA-256/PE header: PASS\n");
            out.append("V8 source-built ARM64 services.exe APK SHA-256/PE header: PASS\n");
            out.append("V8 APK-native loader/NTDLL/wineserver hashes: PASS\n");
            out.append("V8 child-loader selector: APK nativeLibraryDir; v6 NTDLL-only loader\n");
            out.append("V8 PE/NLS paths: source-isolated, matched v6 selectors\n");
        } catch (Exception e) {
            return shortReport(out.append("RESULT: BLOCKED — V16 source preflight: ")
                      .append(e.getClass().getSimpleName()).append('\n'));
        }

        Process serverProc = null, peProc = null, scProc = null;
        File serverLog = null, peLog = null, scLog = null;
        File scratch = null;
        try {
            File privateBase = context.getNoBackupFilesDir().getCanonicalFile();
            File staged = child(privateBase, STAGE_ROOT);
            if (!staged.isDirectory()) throw new SecurityException("Wine29 stage absent");
            scratch = child(privateBase, SCRATCH);
            if (scratch.exists() || !scratch.mkdir())
                throw new SecurityException("V16 one-shot scratch exists or cannot be created; NO retry");
            if (!scratch.getCanonicalFile().getParentFile().equals(privateBase))
                throw new SecurityException("V16 private scratch parent changed");
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
            out.append("Fresh v16 scratch: 34 hybrid DLLs + ARM64 wineboot.exe + 76 NLS hashes PASS\n");
            File bootBuiltin=child(lib,"wineboot.exe");
            if (!bootBuiltin.isFile()
                    || !bootBuiltin.getCanonicalFile().equals(bootBuiltin.getAbsoluteFile())
                    || bootBuiltin.length()!=boot.length())
                throw new SecurityException("V6 source-matched builtin Wineboot alias missing");
            File serviceBuiltin=child(lib,"services.exe");
            if (serviceBuiltin.exists() || serviceBuiltin.isFile() || serviceBuiltin.isDirectory())
                throw new SecurityException("V8 services.exe target unexpectedly exists");
            try (FileOutputStream dst=new FileOutputStream(serviceBuiltin)) {
                dst.write(servicesImage);
            }
            MessageDigest serviceDigest=MessageDigest.getInstance("SHA-256");
            try(InputStream src=new FileInputStream(serviceBuiltin)) {
                byte[] buf=new byte[16384]; int n;
                while((n=src.read(buf))!=-1) serviceDigest.update(buf,0,n);
            }
            String serviceExpected=hex(MessageDigest.getInstance("SHA-256").digest(servicesImage));
            if (serviceBuiltin.length()!=servicesImage.length
                    || !serviceExpected.equals(hex(serviceDigest.digest()))
                    || !serviceBuiltin.getCanonicalFile().getParentFile()
                          .equals(bootBuiltin.getCanonicalFile().getParentFile()))
                throw new SecurityException("V7 services.exe source hash or builtin sibling layout mismatch");
            out.append("V16 source-matched services.exe copied beside Wineboot/kernel32: SHA-256 PASS\n");            File userenvBuiltin=child(lib,"userenv.dll");
            if (userenvBuiltin.exists() || userenvBuiltin.isFile() || userenvBuiltin.isDirectory())
                throw new SecurityException("V8 userenv.dll target already present; sealed 34 DLL mismatch");
            if (userenvImage==null || userenvImage.length<1024)
                throw new SecurityException("V8 verified userenv.dll candidate missing");
            try (FileOutputStream dst=new FileOutputStream(userenvBuiltin)) {
                dst.write(userenvImage);
                dst.getFD().sync();
            }
            MessageDigest userenvDigest=MessageDigest.getInstance("SHA-256");
            try (InputStream src=new FileInputStream(userenvBuiltin)) {
                byte[] buf=new byte[16384]; int n;
                while ((n=src.read(buf))!=-1) userenvDigest.update(buf,0,n);
            }
            String userenvExpected=hex(MessageDigest.getInstance("SHA-256").digest(userenvImage));
            if (userenvBuiltin.length()!=userenvImage.length
                    || !userenvExpected.equals(hex(userenvDigest.digest()))
                    || !userenvBuiltin.getCanonicalFile().getParentFile()
                          .equals(bootBuiltin.getCanonicalFile().getParentFile()))
                throw new SecurityException("V8 userenv.dll SHA-256 or builtin sibling layout mismatch");
            out.append("V8 verified userenv.dll copied beside services/kernel32: SHA-256 PASS\n");
            // New source-built SCM query program; never write or look up v8's prefix.
            File scBuiltin=child(lib,"sc.exe");
            if (scBuiltin.exists() || scBuiltin.isFile() || scBuiltin.isDirectory())
                throw new SecurityException("V16 sc.exe target already exists");
            if (scImage==null || scImage.length<1024)
                throw new SecurityException("V16 source-verified SCM executable absent");
            try(FileOutputStream dst=new FileOutputStream(scBuiltin)) {
                dst.write(scImage);dst.getFD().sync();
            }
            MessageDigest scDigest=MessageDigest.getInstance("SHA-256");
            try(InputStream input=new FileInputStream(scBuiltin)) {
                byte[] buf=new byte[16384];int n;
                while((n=input.read(buf))!=-1)scDigest.update(buf,0,n);
            }
            String expectedSc=hex(MessageDigest.getInstance("SHA-256").digest(scImage));
            if (scBuiltin.length()!=scImage.length || !expectedSc.equals(hex(scDigest.digest()))
                || !scBuiltin.getCanonicalFile().getParentFile().equals(lib.getCanonicalFile()))
                throw new SecurityException("V16 sc.exe scratch source SHA-256 mismatch");
            out.append("V16 verified DLL-tree sc.exe copied next to Wineboot/kernel32: SHA-256 PASS\n");

            out.append("V8 built-in auto-init Wineboot copy: ")
                .append("aarch64-windows/wineboot.exe SHA-256 PASS\n");
            // V3 proved the matched PE directory fixes --help. V6 keeps the exact
            // executable, sealed DLL and selector layout, changing only
            // the explicitly authorized argument to -i in brand-new scratch.
            out.append("V8 explicit Wineboot -i executable: aarch64-windows/wineboot.exe (source-verified, matched DLL directory)\n");
            out.append("V8 experiment: new private C: map and source-verified native child re-exec; direct -i\n");
            File rootDir=child(scratch,"runtime/lib/wine");
            File kernel=child(lib,"kernel32.dll");
            if (!kernel.isFile() || !kernel.getCanonicalFile().equals(kernel.getAbsoluteFile()))
                throw new SecurityException("V6 ARM64 kernel32 file absent from Wine lookup layout");
            if (!bootBuiltin.getCanonicalFile().getParentFile()
                     .equals(kernel.getCanonicalFile().getParentFile()))
                throw new SecurityException("Wine29 v6 EXE and kernel32 must share verified PE directory");
            out.append("V8 PE machine lookup: ARM64, search suffix /aarch64-windows\n");
            out.append("V16 WINEDLLPATH: isolated scratch-local verified PE root (path redacted)\n");
            out.append("V8 kernel32 PE: verified aarch64-windows/kernel32.dll present\n");
            out.append("V16 prior Wine29 v1-v15 scratch directories: NOT ACCESSED; independent new scratch\n");
            File prefix=child(scratch,"prefix");
            mkdir(prefix);
            for (String p:new String[]{"home","tmp","cache","config","xdg-runtime"})
                mkdir(child(scratch,p));
            File cLink=prepareFreshDriveC(prefix);
            out.append("V16 PRESEEDED private drive_c: true (not a Wine result)\n");
            out.append("V16 PRESEEDED dosdevices/c: -> ../drive_c: true (not a Wine result)\n");
            out.append("V8 Windows/users/program-file folders NOT precreated: true\n");
            // V6 explicitly requests -i; Wine may internally attempt auto --init as well.
            // A foreground server supplies a known-good socket before PE startup.
            serverLog=child(scratch,"v16-foreground-wineserver.log");
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
            out.append("V16 foreground wineserver socket observed: ").append(live[0]).append('\n');
            out.append("V16 foreground wineserver lock observed: ").append(live[1]).append('\n');
            out.append("V16 foreground server startup timeout: ").append(serverTimedOut).append('\n');
            out.append("V16 foreground server log cap exceeded: ").append(serverOverflow).append('\n');
            if (live[0]&&live[1]&&serverProc.isAlive()&&!serverOverflow) {
                peLog=child(scratch,"v16-wine-direct-init.log");
                ProcessBuilder p=new ProcessBuilder(loader.getAbsolutePath(),
                                                   bootBuiltin.getAbsolutePath(),"-i");
                p.directory(scratch);
                p.redirectErrorStream(true);
                p.redirectOutput(peLog);
                Map<String,String> initEnv = cleanEnv(p,nativeDir,server,scratch,prefix,lib);
                if (initEnv.containsKey("WINEBOOTSTRAPMODE"))
                    throw new SecurityException("Explicit Wineboot -i inherited bootstrap mode");
                out.append("V16 direct-init launcher WINEBOOTSTRAPMODE: UNSET (verified)\n");
                out.append("Wine may itself enable bootstrap mode for internal auto --init; v6 does not globally override it\n");
                peProc=p.start();
                boolean finished=false, expired=false, overflow=false;
                int exit=-999;
                long start=System.nanoTime();
                while (!finished && !expired && !overflow) {
                    finished=peProc.waitFor(200,TimeUnit.MILLISECONDS);
                    if (finished) exit=peProc.exitValue();
                    overflow=peLog.length()>2L*1024L*1024L;
                    expired=System.nanoTime()-start>=TimeUnit.SECONDS.toNanos(45);
                }
                if (peProc.isAlive()) {
                    peProc.destroyForcibly();
                    peProc.waitFor(2,TimeUnit.SECONDS);
                }
                String peText=boundedLog(peLog);
                boolean createdDriveC=child(prefix,"drive_c").isDirectory();
                boolean systemReg=child(prefix,"system.reg").isFile();
                boolean userReg=child(prefix,"user.reg").isFile();
                boolean userdefReg=child(prefix,"userdef.reg").isFile();
                boolean internalCreationFail=peText.contains("run_wineboot failed to start wineboot");
                boolean childExecFailed=peText.contains("CHAROITE_WINE29_V6_CHILD_EXECV_FAILURE");
                out.append("V16 native child execv errno marker: ").append(childExecFailed)
                    .append(" (absence does not prove child success)\n");
                boolean cLinkRetained = OsConstants.S_ISLNK(Os.lstat(cLink.getAbsolutePath()).st_mode)
                    && "../drive_c".equals(Os.readlink(cLink.getAbsolutePath()))
                    && cLink.getCanonicalFile().equals(child(prefix,"drive_c").getCanonicalFile());
                boolean windows=child(prefix,"drive_c/windows").isDirectory();
                boolean system32=child(prefix,"drive_c/windows/system32").isDirectory();
                boolean users=child(prefix,"drive_c/users").isDirectory();
                boolean appdata=child(prefix,"drive_c/users/xuser/AppData").isDirectory();
                boolean programs=child(prefix,"drive_c/Program Files").isDirectory();
                out.append("V8 C: relative symlink retained: ").append(cLinkRetained).append('\n');
                out.append("V16 Windows-created drive_c/windows: ").append(windows).append('\n');
                out.append("V16 Windows-created drive_c/windows/system32: ").append(system32).append('\n');
                out.append("V16 Windows-created drive_c/users: ").append(users).append('\n');
                out.append("V16 Windows-created drive_c/users/xuser/AppData: ").append(appdata).append('\n');
                out.append("V16 Windows-created drive_c/Program Files: ").append(programs).append('\n');
                out.append("V16 private prefix/drive_c directory present (PRESEEDED): ").append(createdDriveC).append('\n');
                out.append("V16 private prefix/system.reg present: ").append(systemReg).append('\n');
                out.append("V16 private prefix/user.reg present: ").append(userReg).append('\n');
                out.append("V16 private prefix/userdef.reg present: ").append(userdefReg).append('\n');
                out.append("V8 internal auto-init child-creation failure marker: ")
                   .append(internalCreationFail).append('\n');
                out.append("V16 PE trace kernel32.dll mentioned: ").append(peText.toLowerCase(Locale.US).contains("kernel32.dll")).append('\n');
                out.append("V8 PE services.exe mention: ")
                    .append(peText.contains("services.exe")).append('\n');
                out.append("V8 PE cannot find builtin library marker: ")
                    .append(peText.contains("cannot find builtin library for")).append('\n');
                out.append("V16 PE trace c0000135 seen: ").append(peText.toLowerCase(Locale.US).contains("c0000135")).append('\n');
                out.append("V16 PE trace attempted aarch64-windows/kernel32: ")
                   .append(peText.contains("aarch64-windows\\kernel32.dll")
                           || peText.contains("aarch64-windows/kernel32.dll")).append('\n');
                out.append("V16 PE trace attempted old arm64-windows/kernel32: ")
                   .append(peText.contains("arm64-windows\\kernel32.dll")
                           || peText.contains("arm64-windows/kernel32.dll")).append('\n');
                out.append("V16 PE trace bootstrap-mode text seen: ").append(peText.contains("WINEBOOTSTRAPMODE")).append(" (absence not proof of mode)\n");
                out.append("Windows PE attempted: true (source-verified Wineboot -i; separate no-argument sc.exe PE entry may follow; no games)\n");
                out.append("Direct -i PE process completed within 45s: ").append(finished).append('\n');
                out.append("PE exit code: ").append(finished?Integer.toString(exit):"BOUNDED STOP").append('\n');
                out.append("PE 45s deadline exceeded: ").append(expired).append('\n');
                out.append("PE log 2MiB cap exceeded: ").append(overflow).append('\n');
                out.append("V16 direct Wineboot -i source verified invocation: true\n");
                out.append("V8 launcher bootstrap override: none\n");
                out.append("Foreground server alive after PE process: ").append(serverProc.isAlive()).append('\n');
                out.append("V16 PE trace retained locally; raw process lines/paths NOT copied to report\n");

                // V16 tests the source-pinned ARM64 sc.exe via its private Windows C: path
                // BEFORE any native --version probe. The V11 server went away
                // after version comparison; the exact cause is unknown.
                // One Windows PE target, NO sc.exe subcommands, NO SCM query or retries. Capture native ProcessBuilder handoff independently.
                boolean serverBeforeSc = serverProc.isAlive();
                out.append("V16 native --version probes: NOT ATTEMPTED (avoids V11 ordering ambiguity)\n");
                out.append("V16 foreground server alive immediately before sc.exe: ")
                   .append(serverBeforeSc).append('\n');
                if (finished && exit==0 && !expired && !overflow && serverBeforeSc) {
                    // Only V16 scratch: copy the same source-verified ARM64 PE into
                    // the private Windows-created C:\windows\system32, and call
                    // its Windows DOS path instead of V13's Unix absolute path.
                    // C: was PRESEEDED inside V16; never follow external links.
                    File privateSystem32=child(prefix,"drive_c/windows/system32");
                    if (!privateSystem32.isDirectory()
                            || !privateSystem32.getCanonicalFile().equals(privateSystem32.getAbsoluteFile()))
                        throw new SecurityException("V16 Wine-created private system32 missing or linked");
                    File cSc=child(prefix,"drive_c/windows/system32/sc.exe");
                    if (cSc.exists() || cSc.isFile() || cSc.isDirectory())
                        throw new SecurityException("V16 Windows sc.exe target already exists");
                    try(FileOutputStream dst=new FileOutputStream(cSc)) {
                        dst.write(scImage);
                        dst.getFD().sync();
                    }
                    MessageDigest v16Digest=MessageDigest.getInstance("SHA-256");
                    try(InputStream input=new FileInputStream(cSc)) {
                        byte[] chunk=new byte[16384];
                        int n;
                        while((n=input.read(chunk))!=-1)v16Digest.update(chunk,0,n);
                    }
                    if (!cSc.isFile() || cSc.length()!=scImage.length
                            || !expectedSc.equals(hex(v16Digest.digest()))
                            || !cSc.getCanonicalFile().getParentFile().equals(privateSystem32))
                        throw new SecurityException("V16 private Windows sc.exe copy SHA-256 mismatch");
                    out.append("V16 private Windows system32/sc.exe SHA-256: PASS (NEW v16 scratch only)\n");
                    out.append("V16 sc.exe launch form: WINDOWS C:\\windows\\system32\\sc.exe (not Unix path)\n");
                    scLog=child(scratch,"v16-sc-entry.log");
                    ProcessBuilder entry=new ProcessBuilder(loader.getAbsolutePath(),
                                                          "C:\\windows\\system32\\sc.exe");
                    entry.directory(scratch);
                    entry.redirectErrorStream(true);
                    entry.redirectOutput(scLog);
                    Map<String,String> scEnv=cleanEnv(entry,nativeDir,server,scratch,prefix,lib);
                    // V16 preserves V15's Windows C: path and NOEXEC=1.
                    // Adds a bounded native ProcessBuilder boundary observation;
                    // the V12-V15 2x2 comparison was inconclusive.
                    if (!"1".equals(scEnv.get("WINELOADERNOEXEC"))
                            || scEnv.containsKey("WINEBOOTSTRAPMODE"))
                        throw new SecurityException("V16 scoped Windows-path NOEXEC=1 gate failed");
                    out.append("V16 sc.exe WINELOADERNOEXEC: 1 (verified); Windows C: path retained\n");
                    // Android accepting a native subprocess is NOT evidence PE mapped.
                    out.append("V16 verified APK-native loader canExecute: ")
                       .append(loader.canExecute()).append('\n');
                    long nativeStart=System.nanoTime();
                    try {
                        scProc=entry.start();
                        out.append("V16 Android ProcessBuilder.start: RETURNED PROCESS (native accepted; Windows PE unverified)\n");
                    } catch (java.io.IOException launchError) {
                        out.append("V16 Android ProcessBuilder.start: THREW ")
                           .append(launchError.getClass().getSimpleName()).append('\n');
                        Throwable cause=launchError.getCause();
                        if (cause instanceof android.system.ErrnoException)
                            out.append("V16 Android exec errno: ")
                               .append(((android.system.ErrnoException)cause).errno).append('\n');
                        throw launchError;
                    }
                    out.append("V16 Android native launch acceptance latency ms: ")
                       .append(TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-nativeStart)).append('\n');
                    out.append("V16 foreground server alive after native process accepted: ")
                       .append(serverProc.isAlive()).append('\n');
                    boolean scFinished=false, scDeadline=false, scOverflow=false;
                    int scExit=-999;
                    long scBegin=System.nanoTime();
                    while (!scFinished && !scDeadline && !scOverflow) {
                        scFinished=scProc.waitFor(200,TimeUnit.MILLISECONDS);
                        if (scFinished) scExit=scProc.exitValue();
                        scOverflow=scLog.length()>512L*1024L;
                        scDeadline=System.nanoTime()-scBegin>=TimeUnit.SECONDS.toNanos(12);
                    }
                    if (scProc.isAlive()) {
                        scProc.destroyForcibly();
                        scProc.waitFor(2,TimeUnit.SECONDS);
                    }
                    out.append("V16 native process elapsed ms (start to bounded exit/stop): ")
                       .append(TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-nativeStart)).append('\n');
                    out.append("V16 foreground server alive at native process completion: ")
                       .append(serverProc.isAlive()).append('\n');
                    long scBytes=scLog.length();
                    String scOutput=boundedLog(scLog).toLowerCase(Locale.US);
                    out.append("V16 sc.exe Windows-path PE-entry attempted: true\n");
                    out.append("V16 sc.exe process completed within 12s: ").append(scFinished).append('\n');
                    out.append("V16 sc.exe subprocess exit: ").append(scFinished?scExit:"BOUNDED STOP").append('\n');
                    if (scFinished && scExit==127)
                        out.append("V16 sc.exe exit 127: cause still unproven; PE mapping not established\n");
                    out.append("V16 sc.exe output bytes: ").append(scBytes).append('\n');
                    out.append("V16 sc.exe output log cap exceeded: ").append(scOverflow).append('\n');
                    out.append("V16 sc.exe usage marker: ")
                        .append(scOutput.contains("usage")||scOutput.contains("service control")).append('\n');
                    out.append("V16 foreground server alive immediately after sc.exe: ")
                        .append(serverProc.isAlive()).append('\n');
                    out.append("V16 sc.exe PE mapping: UNVERIFIED; ProcessBuilder success/exit 127 cannot establish Windows PE entry\n");
                    out.append("V16 SCM query / service operation: NOT ATTEMPTED\n");
                    out.append("V16 PE/server logs: PRESERVED LOCALLY, no raw paths copied\n");
                } else {
                    out.append("V16 sc.exe PE-entry attempted: false — Wineboot gate or foreground server unavailable\n");
                    out.append("V16 SCM query / service operation: NOT ATTEMPTED\n");
                }
                if (finished&&exit==0&&cLinkRetained&&windows&&system32&&users
                        &&!internalCreationFail&&!expired&&!overflow)
                    out.append("RESULT: PARTIAL — Wineboot created folders; V16 sc.exe entry separately observed; SCM NOT TESTED\n");
                else if (finished&&exit==0&&cLinkRetained&&windows&&system32&&users
                        &&!expired&&!overflow)
                    out.append("RESULT: PARTIAL — Wine-created Windows folders; possible internal child issue; SCM NOT TESTED\n");
                else
                    out.append("RESULT: INCOMPLETE — Wineboot/PE gate not met; V16 entry evidence retained\n");
            } else {
                out.append("Windows PE attempted: false — foreground server was not ready\n");
                out.append("RESULT: FAIL — V16 private server handshake unavailable; no -i attempted\n");
            }
        } catch (Exception e) {
            out.append("RESULT: BLOCKED — ").append(e.getClass().getSimpleName())
               .append("; error details retained locally; no old data accessed\n");
        } finally {
            try {
                if (scProc!=null&&scProc.isAlive()) {
                    scProc.destroyForcibly(); scProc.waitFor(2,TimeUnit.SECONDS);
                }
                if (peProc!=null&&peProc.isAlive()) {
                    peProc.destroyForcibly(); peProc.waitFor(2,TimeUnit.SECONDS);
                }
                if (serverProc!=null&&serverProc.isAlive()) {
                    serverProc.destroyForcibly(); serverProc.waitFor(2,TimeUnit.SECONDS);
                }
                out.append("Foreground v16 server terminated if running; no other prefix/server targeted\n");
                if (serverLog!=null) {
                    String serverText=boundedLog(serverLog);
                    out.append("V16 server trace internal auto-init marker observed: ")
                       .append(serverText.contains("--init")).append(" (absence not proof it did not run)\n");
                    out.append("V16 server trace retained locally; raw lines/paths NOT copied\n");
                }
            } catch (Exception e) {
                out.append("V16 finalization diagnostics: ")
                   .append(e.getClass().getSimpleName()).append('\n');
            }
        }
        if (scratch!=null && scratch.isDirectory()) {
            try {
                File prefix=child(scratch,"prefix");
                for(String reg:new String[]{"system.reg","user.reg","userdef.reg"}) {
                    File f=child(prefix,reg);
                    out.append("V16 retained ").append(reg).append(" metadata: ")
                       .append(f.isFile() ? f.length() + " bytes" : "absent")
                       .append("; contents NOT read\n");
                }
            } catch(Exception ignored) {
                out.append("V16 registry metadata could not be read; contents NOT accessed\n");
            }
        }
        out.append("V16 scratch retained; NEVER retry or delete V16 after first use\n");
        out.append("Wine28, Wine29 v1–v15, stable Portal, original Wine and game saves: UNCHANGED\n");
        return shortReport(out);
    }
}
