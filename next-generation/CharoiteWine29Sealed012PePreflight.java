package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.TreeSet;

/**
 * Read-only Wine29 .0.12 PE bootstrap layout / static import preflight.
 * This NEVER launches Wine, wineserver, Wineboot, PE, an app or a shell;
 * it neither creates a prefix nor modifies even its own staging slot.
 * Stage.verifyOnly is the independently hash-checked sealed inventory gate.
 * An imported DLL absent from the 34 packaged PE modules is diagnostic
 * evidence, NOT definitive proof that a native Wine resolver cannot supply it.
 */
public final class CharoiteWine29Sealed012PePreflight {
    private static final String PACKAGE = "com.charoitx";
    private static final String ROOT = "charoite-next-wine29-012-sealed-pe-nls";
    private static final String SLOT = "wine10-arm64ec-dependencies-0.12-sealed-pe-nls";
    private static final int ARM64EC = 0xa641;
    private static final int ARM64 = 0xaa64;
    private static final int MAX_PE = 32 * 1024 * 1024;
    private static final int MAX_IMPORTS = 256;
    private CharoiteWine29Sealed012PePreflight() {}

    private static int u16(byte[] data, int off) {
        if (off < 0 || off > data.length - 2)
            throw new SecurityException("PE header outside verified file");
        return (data[off] & 255) | ((data[off + 1] & 255) << 8);
    }

    private static long u32(byte[] data, int off) {
        return Integer.toUnsignedLong(u16(data, off) | (u16(data, off + 2) << 16));
    }

    private static byte[] read(File file) throws Exception {
        if (!file.isFile() || file.length() <= 0 || file.length() > MAX_PE ||
            !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Unsafe staged Wine29 PE path/size");
        ByteArrayOutputStream bytes = new ByteArrayOutputStream((int)file.length());
        try (InputStream in = new FileInputStream(file)) {
            byte[] chunk = new byte[32768];
            int n;
            while ((n = in.read(chunk)) != -1) {
                if (bytes.size() + n > MAX_PE)
                    throw new SecurityException("Oversized Wine29 PE");
                bytes.write(chunk, 0, n);
            }
        }
        if (bytes.size() != file.length())
            throw new SecurityException("Staged Wine29 PE changed during preflight");
        return bytes.toByteArray();
    }

    private static int rva(byte[] data, int sections, int count, long target) {
        for (int i = 0; i < count; i++) {
            int at = sections + 40 * i;
            long virtualSize = u32(data, at + 8);
            long virtualAddress = u32(data, at + 12);
            long rawSize = u32(data, at + 16);
            long rawOffset = u32(data, at + 20);
            if (target >= virtualAddress &&
                target - virtualAddress < Math.max(virtualSize, rawSize) &&
                target - virtualAddress < rawSize) {
                long position = rawOffset + target - virtualAddress;
                if (position >= 0 && position < data.length)
                    return (int)position;
            }
        }
        throw new SecurityException("Wine29 import RVA does not map into file");
    }

    private static String importName(byte[] data, int start) {
        StringBuilder name = new StringBuilder();
        for (int i = 0; i < 96; i++) {
            if (start + i >= data.length)
                throw new SecurityException("Unterminated Wine29 imported module name");
            int ch = data[start + i] & 255;
            if (ch == 0) {
                String value = name.toString().toLowerCase(Locale.US);
                if (!value.matches("[a-z0-9_.+-]{1,96}"))
                    throw new SecurityException("Invalid Wine29 PE import name");
                return value;
            }
            if (ch < 32 || ch > 126)
                throw new SecurityException("Non-ASCII Wine29 PE import name");
            name.append((char)ch);
        }
        throw new SecurityException("Wine29 PE import name exceeds bound");
    }

    private static int inspect(File file, int expectedMachine, Set<String> imports,
                               int[] rawMachineCounts) throws Exception {
        byte[] data = read(file);
        if (u16(data, 0) != 0x5a4d)
            throw new SecurityException("Wine29 staged image is not MZ");
        long peLong = u32(data, 0x3c);
        if (peLong > data.length - 24)
            throw new SecurityException("Wine29 PE header offset invalid");
        int pe = (int)peLong;
        long signature = u32(data, pe);
        int rawMachine = u16(data, pe + 4);
        // Hybrid ARM64X DLLs expose an ARM64EC view verified in the source
        // build, but their raw COFF machine may be AA64 or A641.
        // Regular ARM64 wineboot.exe remains restricted to AA64.
        boolean accepted = expectedMachine == ARM64EC
            ? (rawMachine == ARM64EC || rawMachine == ARM64)
            : rawMachine == expectedMachine;
        if (signature != 0x00004550L || !accepted)
            throw new SecurityException("Wine29 PE signature or architecture mismatch: " +
                file.getName() + " signature=0x" + Long.toHexString(signature) +
                " rawMachine=" + String.format(Locale.US, "0x%04X", rawMachine) +
                " expected=" + (expectedMachine == ARM64EC ?
                    "ARM64EC-view hybrid (raw AA64/A641)" : "ARM64 (raw AA64)"));
        if (expectedMachine == ARM64EC)
            rawMachineCounts[rawMachine == ARM64 ? 0 : 1]++;
        int sectionCount = u16(data, pe + 6);
        int optionalSize = u16(data, pe + 20);
        int opt = pe + 24;
        if (sectionCount <= 0 || sectionCount > 96 ||
            optionalSize < 128 || u16(data, opt) != 0x20b ||
            (long)opt + optionalSize + (long)sectionCount * 40 > data.length)
            throw new SecurityException("Invalid Wine29 PE32+ section/optional header");
        int sections = opt + optionalSize;
        if (u32(data, opt + 108) < 2)
            throw new SecurityException("Missing Wine29 PE data-directory metadata");
        long importRva = u32(data, opt + 120);
        long importSize = u32(data, opt + 124);
        if (importRva == 0 && importSize == 0) return 0;
        if (importRva == 0 || importSize < 20 || importSize > MAX_PE)
            throw new SecurityException("Malformed Wine29 PE import-directory size");
        int off = rva(data, sections, sectionCount, importRva);
        int names = 0;
        boolean terminated = false;
        for (int i = 0; i < MAX_IMPORTS; i++) {
            int at = off + i * 20;
            if (at < 0 || at > data.length - 20 ||
                (long)(i + 1) * 20 > importSize)
                throw new SecurityException("Truncated Wine29 PE import descriptors");
            long lookup = u32(data, at);
            long date = u32(data, at + 4);
            long forwarder = u32(data, at + 8);
            long name = u32(data, at + 12);
            long thunk = u32(data, at + 16);
            if ((lookup | date | forwarder | name | thunk) == 0) {
                terminated = true;
                break;
            }
            if (name == 0)
                throw new SecurityException("Unnamed Wine29 PE import descriptor");
            imports.add(importName(data, rva(data, sections, sectionCount, name)));
            names++;
        }
        if (!terminated)
            throw new SecurityException("Wine29 import-descriptor termination absent");
        return names;
    }


    /**
     * Read actual IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT (index 13); 32-byte
     * descriptors. These are potential dependencies, NOT proven startup needs.
     * Independent of ordinary imports, with bounded offsets and termination.
     */
    private static int inspectDelayed(File file, Set<String> delayed) throws Exception {
        byte[] data = read(file);
        if (u16(data, 0) != 0x5a4d)
            throw new SecurityException("Wine29 delay PE DOS signature absent");
        long peLong = u32(data, 0x3c);
        if (peLong > data.length - 24 || peLong < 64 ||
            u32(data, (int)peLong) != 0x00004550L)
            throw new SecurityException("Wine29 invalid PE delay header");
        int pe = (int)peLong;
        int sectionCount = u16(data, pe + 6);
        int optionalSize = u16(data, pe + 20);
        int opt = pe + 24;
        if (sectionCount <= 0 || sectionCount > 96 ||
            optionalSize < 224 || u16(data, opt) != 0x20b ||
            (long)opt + optionalSize + (long)sectionCount * 40 > data.length)
            throw new SecurityException("Invalid Wine29 delay-load optional header");
        int sections = opt + optionalSize;
        if (u32(data, opt + 108) <= 13)
            return 0;
        int delayDir = opt + 112 + 13 * 8;
        if (delayDir + 8 > sections)
            throw new SecurityException("Missing delay import data directory");
        long delayRva = u32(data, delayDir);
        long delaySize = u32(data, delayDir + 4);
        if (delayRva == 0 && delaySize == 0) return 0;
        if (delayRva == 0 || delaySize < 32 || delaySize > 1000000)
            throw new SecurityException("Invalid Wine29 delay directory size");
        int at = rva(data, sections, sectionCount, delayRva);
        long base = u32(data, opt + 24) | (u32(data, opt + 28) << 32);
        int total = 0;
        boolean terminated = false;
        for (int i = 0; i < MAX_IMPORTS; i++) {
            int loc = at + i * 32;
            if (loc < 0 || loc > data.length - 32 ||
                (long)(i + 1) * 32 > delaySize)
                throw new SecurityException("Truncated Wine29 delay-load descriptors");
            long mask = 0;
            for (int j = 0; j < 8; j++) mask |= u32(data, loc + 4*j);
            if (mask == 0) { terminated = true; break; }
            long attrs = u32(data, loc);
            long name = u32(data, loc + 4);
            if ((attrs & 1) == 0) {
                if (Long.compareUnsigned(name, base) < 0)
                    throw new SecurityException("Invalid Wine29 delay-load VA");
                name -= base;
            }
            if (name <= 0 || name >= 0x100000000L)
                throw new SecurityException("Unmapped Wine29 delayed DLL name");
            delayed.add(importName(data, rva(data, sections, sectionCount, name)));
            total++;
        }
        if (!terminated) throw new SecurityException("Wine29 delay-load descriptor terminator missing");
        return total;
    }

    /** All paths are inferred from the OWN sealed staging slot only. */
    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — WINE29 .0.12 PE BOOTSTRAP STATIC PREFLIGHT\n");
        out.append("READ ONLY; no Wine/Wineboot/PE/wineserver execution or prefix/scratch writes\n");
        out.append("Wine28 v1–v9, stable Portal, games, saves and rootfs: NOT ACCESSED\n");
        try {
            if (!PACKAGE.equals(context.getPackageName()))
                throw new SecurityException("Wrong Android package");
            String report = CharoiteWine29Sealed012Stage.verifyOnly(context);
            if (!report.contains(
                "RESULT: PASS — isolated Wine29 0.12 data-only stage; NOT RUNNABLE"))
                throw new SecurityException("Sealed Wine29 source/staged SHA audit did not pass");

            File base = context.getNoBackupFilesDir().getCanonicalFile();
            File slot = new File(new File(base, ROOT), SLOT);
            if (!slot.getCanonicalFile().equals(slot.getAbsoluteFile()) ||
                !slot.getCanonicalFile().toPath().startsWith(base.toPath()))
                throw new SecurityException("Wine29 scratch selector path escaped private storage");
            File pe = new File(new File(slot, "pe"), "arm64ec");
            File nls = new File(slot, "nls");
            File wineboot = new File(new File(new File(slot, "pe"), "arm64"), "wineboot.exe");
            File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            if (!pe.isDirectory() || !nls.isDirectory() || !nativeDir.isDirectory())
                throw new SecurityException("Wine29 mandatory PE/NLS/native selector directory missing");
            for (String filename : new String[] {
                    "libcharoite_wine29_loader.so", "libcharoite_wine29_wineserver.so",
                    "libcharoite_wine29_ntdll.so" }) {
                if (!new File(nativeDir, filename).isFile())
                    throw new SecurityException("Missing source-matched Wine29 native ELF");
            }
            File[] dlls = pe.listFiles();
            if (dlls == null || dlls.length != 34)
                throw new SecurityException("Wine29 must have exactly 34 sealed ARM64EC DLLs");
            Set<String> packaged = new HashSet<>();
            Set<String> imported = new TreeSet<>();
            Set<String> delayed = new TreeSet<>();
            int delayedImports = 0;
            int directImports = 0;
            int[] rawMachineCounts = new int[2]; // [AA64 hybrid raw, A641 raw]
            for (File dll : dlls) {
                String filename = dll.getName();
                if (!filename.matches("[a-z0-9_]+\\.dll") ||
                    !packaged.add(filename))
                    throw new SecurityException("Unapproved Wine29 PE module filename");
                directImports += inspect(dll, ARM64EC, imported, rawMachineCounts);
                delayedImports += inspectDelayed(dll, delayed);
            }
            for (String essential : new String[] {
                    "ntdll.dll", "kernel32.dll", "apisetschema.dll" })
                if (!packaged.contains(essential))
                    throw new SecurityException("Essential Wine29 PE module missing: " + essential);
            directImports += inspect(wineboot, ARM64, imported, rawMachineCounts);
            delayedImports += inspectDelayed(wineboot, delayed);
            Set<String> external = new TreeSet<>(imported);
            external.removeAll(packaged);
            Set<String> deferredOutside = new TreeSet<>(delayed);
            deferredOutside.removeAll(packaged);
            if (directImports != 186 || !external.isEmpty() || delayedImports != 68 ||
                deferredOutside.size() != 15)
                throw new SecurityException("Wine29 0.12 phone PE import closure differs from source-attested baseline: " +
                    "regular=" + directImports + " unbundledRegular=" + external.size() +
                    " delayed=" + delayedImports + " unbundledDelay=" + deferredOutside.size());
            out.append("Native selector: original Wine29 0.7 source-matched APK ELF trio verified\n");
            out.append("PE selector: isolated slot/pe/arm64ec, 34 source-verified ARM64EC-view hybrid DLL headers PASS\n");
            out.append("Raw COFF machines among 34 DLLs: AA64=")
               .append(rawMachineCounts[0]).append(" A641=")
               .append(rawMachineCounts[1]).append('\n');
            out.append("DATA selector: isolated slot parent, 76 NLS files SHA-256 PASS\n");
            out.append("wineboot.exe header: separate ARM64 PE32+ PASS; NOT EXECUTED\n");
            out.append("Static PE import descriptors inspected: ").append(directImports).append('\n');
            out.append("Distinct referenced DLL names: ").append(imported.size()).append('\n');
            out.append("Ordinary imports not in sealed 34-DLL PE cohort: ").append(external.size()).append('\n');
            out.append("Actual delay-load descriptors inspected: ").append(delayedImports).append('\n');
            out.append("Unbundled delay-load DLL names: ").append(deferredOutside.size()).append('\n');
            int deferredShown = 0;
            for (String name : deferredOutside) {
                if (deferredShown++ == 15) break;
                out.append("  deferred: ").append(name).append('\n');
            }
            int shown = 0;
            for (String name : external) {
                if (shown++ == 20) { out.append("  ...remaining names omitted\n"); break; }
                out.append("  ").append(name).append('\n');
            }
            out.append("Delay-load names are diagnostic, NOT proven startup failures\n");
            out.append("Selectors proposed ONLY; environment variables NOT set or executed\n");
            out.append("RESULT: PASS — isolated Wine29 0.12 34-DLL direct/delay PE preflight; NOT RUNNABLE\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ")
                .append(error.getClass().getSimpleName())
                .append(": ").append(error.getMessage()).append('\n');
        }
        return out.toString();
    }
}
