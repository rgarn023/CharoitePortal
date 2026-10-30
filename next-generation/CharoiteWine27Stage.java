package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Explicitly opted-in, source-hash-verified Wine27 data slot.
 * This class NEVER executes native or Windows code. No existing 0.4 slot,
 * Wine prefix, rootfs, games, saves, environment or native binary is touched.
 */
public final class CharoiteWine27Stage {
    private static final String PACKAGE = "com.charoitx";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String VERSION = "wine10-arm64ec-bootstrap.0.5";
    private static final String INDEX = "charoite-next/wine-bootstrap-27-index.json";
    private static final String BUNDLE = "charoite-next/wine-bootstrap-27.bundle";
    private static final String ASSET_ROOT = "charoite-next/wine27-modules/";
    private static final String ROOT = "charoite-next-isolated-wine";
    private static final String FINAL = "wine10-arm64ec-bootstrap-0.6-staged";
    private static final String PENDING = ".wine10-arm64ec-bootstrap-0.6-pending";
    private static final long RUN = 41130899651L;
    private static final long ARTIFACT = 13012239618L;
    private static final long MAX_ARCHIVE = 128L * 1024L * 1024L;
    private static final long MAX_MODULE = 32L * 1024L * 1024L;
    private static final long MAX_TOTAL = 128L * 1024L * 1024L;
    private CharoiteWine27Stage() {}

    private static String sha(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes)
            result.append(String.format(Locale.US,"%02x",b&255));
        return result.toString();
    }

    private static String jsonAsset(Context context) throws Exception {
        try (InputStream input = context.getAssets().open(INDEX)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[2048];
            int n;
            while ((n=input.read(buf))!=-1) {
                if (out.size()+n > 65536)
                    throw new SecurityException("Wine27 index exceeds source limit");
                out.write(buf,0,n);
            }
            return out.toString("UTF-8");
        }
    }

    private static void archiveAudit(Context context, JSONObject index) throws Exception {
        long expectedSize = index.getLong("archive_size");
        String expected = index.getString("archive_sha256");
        if (expectedSize<=0 || expectedSize>MAX_ARCHIVE || !expected.matches("[0-9a-f]{64}"))
            throw new SecurityException("Untrusted Wine27 full archive metadata");
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        long size=0;
        try (InputStream input=context.getAssets().open(BUNDLE)) {
            byte[] bytes=new byte[32768];
            int n;
            while ((n=input.read(bytes))!=-1) {
                size+=n;
                if (size>expectedSize || size>MAX_ARCHIVE)
                    throw new SecurityException("Wine27 archive exceeds audited bound");
                md.update(bytes,0,n);
            }
        }
        if (size!=expectedSize || !expected.equals(sha(md.digest())))
            throw new SecurityException("Wine27 full source archive SHA-256 mismatch");
    }

    private static String approvedPath(String path) {
        if (!(path.matches("pe/arm64ec/[a-z0-9_]+\\.dll")
                || path.equals("pe/arm64/wineboot.exe")
                || path.matches("nls/[a-z_0-9]+\\.nls")))
            throw new SecurityException("Untrusted Wine27 Windows module path");
        return path;
    }

    private static JSONObject validatedInventory(Context context) throws Exception {
        if (!PACKAGE.equals(context.getPackageName()))
            throw new SecurityException("Wrong Android package for Wine27");
        JSONObject index = new JSONObject(jsonAsset(context));
        if (index.getInt("schema_version")!=1
                || !PACKAGE.equals(index.getString("android_package"))
                || !SOURCE.equals(index.getString("wine_source_sha"))
                || index.getLong("source_run")!=RUN
                || index.getLong("source_artifact")!=ARTIFACT
                || !VERSION.equals(index.getString("bundle_version"))
                || !BUNDLE.equals(index.getString("archive_asset"))
                || index.getInt("component_count")!=26
                || index.getInt("pe_count")!=23
                || index.getInt("native_elf_in_archive")!=3
                || index.getInt("nls_count")!=76
                || index.getInt("module_count")!=99
                || index.getInt("remaining_observed_pe_imports_count")!=20
                || index.getBoolean("launch_ready")
                || index.getBoolean("installable_as_runtime")
                || index.getBoolean("native_elf_installed")
                || index.getBoolean("prefix_created")
                || index.getBoolean("wineboot_tested")
                || index.getBoolean("fex_installed")
                || index.getBoolean("graphics_verified")
                || index.getBoolean("anti_cheat_supported"))
            throw new SecurityException("Untrusted Wine27 source readiness or module count");
        JSONArray gaps = index.getJSONArray("remaining_observed_pe_imports");
        if (gaps.length()!=20) throw new SecurityException("Wine27 dependency gap count drift");
        String prior="";
        for (int i=0;i<gaps.length();i++) {
            String name=gaps.getString(i);
            if (!name.matches("[a-z0-9_]+\\.dll") || name.compareTo(prior)<=0)
                throw new SecurityException("Unverified Wine27 import list");
            prior=name;
        }
        JSONArray entries=index.getJSONArray("module_files");
        if (entries.length()!=99 || index.getLong("modules_total_bytes")>MAX_TOTAL)
            throw new SecurityException("Invalid Wine27 file inventory length");
        long size=0;
        int nls=0,pe=0;
        prior="";
        HashSet<String> assets=new HashSet<>();
        for (int i=0;i<entries.length();i++) {
            JSONObject item=entries.getJSONObject(i);
            String path=approvedPath(item.getString("path"));
            if (path.compareTo(prior)<=0) throw new SecurityException("Unsorted Wine27 allowlist");
            prior=path;
            String asset=ASSET_ROOT+path.replace('/','_')+".bin";
            long bytes=item.getLong("size");
            String digest=item.getString("sha256");
            if (!item.getString("source").equals("runtime/"+path)
                    || !asset.equals(item.getString("asset"))
                    || !assets.add(asset)
                    || bytes<=0 || bytes>MAX_MODULE
                    || !digest.matches("[0-9a-f]{64}"))
                throw new SecurityException("Invalid Wine27 module record");
            size+=bytes;
            if (path.startsWith("nls/"))nls++;else pe++;
        }
        if (size!=index.getLong("modules_total_bytes") || size>MAX_TOTAL || nls!=76 || pe!=23)
            throw new SecurityException("Incorrect PE/NLS size or count");
        archiveAudit(context,index);
        return index;
    }

    private static File within(File dir,String path) throws Exception {
        File target=new File(dir,path);
        File root=dir.getCanonicalFile();
        File resolved=target.getCanonicalFile();
        if (root.equals(resolved) || !resolved.toPath().startsWith(root.toPath())
                || !resolved.equals(target.getAbsoluteFile()))
            throw new SecurityException("Wine27 module path escapes versioned slot");
        return target;
    }

    private static boolean hashMatches(File file,long expectedSize,String expected) throws Exception {
        if (!file.isFile() || !file.getCanonicalFile().equals(file.getAbsoluteFile())
                || file.length()!=expectedSize)
            return false;
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        try (InputStream input=new FileInputStream(file)) {
            byte[] buf=new byte[32768];
            int n;
            while ((n=input.read(buf))!=-1) md.update(buf,0,n);
        }
        return expected.equals(sha(md.digest()));
    }

    private static void verify(File slot,JSONArray entries) throws Exception {
        if (!slot.isDirectory()) throw new SecurityException("Missing complete Wine27 data slot");
        for (int i=0;i<entries.length();i++) {
            JSONObject e=entries.getJSONObject(i);
            File target=within(slot,e.getString("path"));
            if (!hashMatches(target,e.getLong("size"),e.getString("sha256")))
                throw new SecurityException("Wine27 data hash mismatch: "+e.getString("path"));
        }
    }

    /**
     * Re-verify already staged Wine27 data with no filesystem mutation.
     * An absent or incomplete 0.5 slot blocks native version-only tests.
     */
    public static String verifyOnly(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — WINE27 STAGED PE/NLS READ-ONLY VERIFY\n");
        out.append("Existing Wine22, prefixes, game saves, rootfs: NOT ACCESSED\n");
        try {
            JSONObject index = validatedInventory(context);
            File base = context.getNoBackupFilesDir().getCanonicalFile();
            File dir = new File(base, ROOT);
            if (!dir.getCanonicalFile().getParentFile().equals(base)
                    || !dir.isDirectory())
                throw new SecurityException("Wine27 private staging root absent");
            File pending = within(dir, PENDING);
            if (pending.exists())
                throw new SecurityException("Incomplete pending Wine27 generation quarantined");
            File complete = within(dir, FINAL);
            verify(complete, index.getJSONArray("module_files"));
            out.append("Source archive SHA-256: PASS\n");
            out.append("Staged Windows PE: 23/23 SHA-256 PASS\n");
            out.append("Staged Wine NLS: 76/76 SHA-256 PASS\n");
            out.append("Native binaries, Wineboot and Windows EXE: NOT EXECUTED\n");
            out.append("RESULT: PASS — Wine27 99-file data gate; NOT runnable\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName()).append("\n");
        }
        return out.toString();
    }

    public static String run(Context context) {
        StringBuilder out=new StringBuilder();
        out.append("CHAROITE NEXT — ISOLATED WINE27 PE/NLS STAGING\n");
        out.append("Scope: source-verified new generation; Windows module DATA ONLY\n");
        out.append("Original Wine22 staging, existing prefixes, games, saves, rootfs: NOT ACCESSED\n");
        out.append("Native ELF in Wine27 archive: INERT; NOT INSTALLED OR EXECUTED\n");
        out.append("Wineboot, wineserver session, Windows EXE, FEX, graphics: NOT ATTEMPTED\n");
        try {
            JSONObject index=validatedInventory(context);
            JSONArray entries=index.getJSONArray("module_files");
            File base=context.getNoBackupFilesDir().getCanonicalFile();
            File dir=new File(base,ROOT);
            if (!dir.getCanonicalFile().getParentFile().equals(base))
                throw new SecurityException("Unexpected private staging root");
            if (!dir.exists() && !dir.mkdir())
                throw new SecurityException("Cannot create isolated Wine27 parent");
            File pending=within(dir,PENDING);
            File complete=within(dir,FINAL);
            if (pending.exists())
                throw new SecurityException("Quarantined partial Wine27 stage; no overwrite attempted");
            if (complete.exists()) {
                verify(complete,entries);
                out.append("Existing Wine27 Windows PE: 23/23 SHA-256 PASS\n");
                out.append("Existing Wine27 NLS: 76/76 SHA-256 PASS\n");
                out.append("RESULT: PASS — existing Wine27 isolated data verified; NOT runnable\n");
                return out.toString();
            }
            if (!pending.mkdir())
                throw new SecurityException("Failed to create Wine27 pending stage");
            byte[] buffer=new byte[32768];
            for (int i=0;i<entries.length();i++) {
                JSONObject item=entries.getJSONObject(i);
                File destination=within(pending,item.getString("path"));
                File parent=destination.getParentFile();
                if ((!parent.exists() && !parent.mkdirs()) || destination.exists())
                    throw new SecurityException("Unsafe Wine27 module destination");
                long remaining=item.getLong("size");
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                try (InputStream input=context.getAssets().open(item.getString("asset"));
                     FileOutputStream output=new FileOutputStream(destination)) {
                    while (remaining>0) {
                        int n=input.read(buffer,0,(int)Math.min((long)buffer.length,remaining));
                        if (n<0) throw new SecurityException("Short verified Wine27 APK asset");
                        if (n==0) continue;
                        output.write(buffer,0,n);
                        digest.update(buffer,0,n);
                        remaining-=n;
                    }
                    if (input.read()!=-1)
                        throw new SecurityException("Unexpected trailing Wine27 module bytes");
                    output.getFD().sync();
                }
                if (!item.getString("sha256").equals(sha(digest.digest())))
                    throw new SecurityException("Wine27 source SHA-256 changed during staging");
            }
            verify(pending,entries);
            if (!pending.renameTo(complete))
                throw new SecurityException("Cannot atomically finalize Wine27 data slot");
            verify(complete,entries);
            out.append("Full 26-component source archive SHA-256: PASS\n");
            out.append("Windows PE data: 23/23 staged and verified\n");
            out.append("Wine NLS data: 76/76 staged and verified\n");
            out.append("Observed unbundled PE import names: 20\n");
            out.append("Original Wine22/native-loader cohort: UNCHANGED\n");
            out.append("RESULT: PASS — source-coherent Wine27 data staged; NOT runnable\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName()).append("\n");
            out.append("No Wine27 executable or prefix started; pending data remains quarantined\n");
        }
        return out.toString();
    }
}
