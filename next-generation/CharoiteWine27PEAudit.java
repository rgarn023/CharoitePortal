package com.charoitegames.core;

import java.io.File;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.TreeSet;

/**
 * Static, read-only PE file header and import-directory inspector.
 * Cannot execute the PE, start Wine, or write to the device.
 * Reports direct imports only; does not imply full module dependency closure.
 */
public final class CharoiteWine27PEAudit {
    private static final long MAX_PE = 32L * 1024 * 1024;
    private CharoiteWine27PEAudit() {}

    private static int u16(RandomAccessFile f, long offset) throws Exception {
        f.seek(offset);
        return f.readUnsignedByte() | (f.readUnsignedByte() << 8);
    }
    private static long u32(RandomAccessFile f, long offset) throws Exception {
        f.seek(offset);
        return (long)f.readUnsignedByte() |
            ((long)f.readUnsignedByte() << 8) |
            ((long)f.readUnsignedByte() << 16) |
            ((long)f.readUnsignedByte() << 24);
    }
    private static long map(long rva, List<long[]> sections) {
        for (long[] s : sections) {
            long local = rva - s[0];
            if (local >= 0 && local < s[1] && local < s[2])
                return s[3] + local;
        }
        return -1;
    }
    private static String ascii(RandomAccessFile f, long offset) throws Exception {
        if (offset < 0 || offset >= f.length()) return "(invalid)";
        f.seek(offset);
        StringBuilder out = new StringBuilder();
        for (int i=0;i<96 && f.getFilePointer()<f.length();i++) {
            int c=f.readUnsignedByte();
            if (c==0) break;
            if (c < 33 || c > 126) return "(non-ascii)";
            out.append((char)c);
        }
        String name=out.toString();
        return name.matches("[A-Za-z0-9_.+-]{1,96}") ? name : "(invalid)";
    }

    public static String inspect(File file, File arm64ecDir, File arm64Dir,
                                 String label) {
        StringBuilder out=new StringBuilder();
        out.append("PE static inspection: ").append(label).append('\n');
        try {
            if (!file.isFile() || file.isDirectory()
                    || !file.getCanonicalFile().equals(file.getAbsoluteFile())
                    || file.length()<128 || file.length()>MAX_PE)
                throw new SecurityException("PE input absent or unsafe");
            try (RandomAccessFile f=new RandomAccessFile(file,"r")) {
                if (u16(f,0)!=0x5a4d) throw new SecurityException("Missing MZ");
                long pe=u32(f,0x3c);
                if (pe<64 || pe>f.length()-24 || u32(f,pe)!=0x00004550L)
                    throw new SecurityException("Invalid PE header offset/signature");
                int machine=u16(f,pe+4);
                int sectionsCount=u16(f,pe+6);
                int optionalBytes=u16(f,pe+20);
                long optional=pe+24;
                if (sectionsCount<1 || sectionsCount>96 || optionalBytes<96
                        || optionalBytes>2048
                        || optional+optionalBytes+40L*sectionsCount>f.length())
                    throw new SecurityException("Invalid PE section boundaries");
                int magic=u16(f,optional);
                if (magic!=0x20b && magic!=0x10b)
                    throw new SecurityException("Unsupported PE optional header");
                out.append(String.format(Locale.US,"Raw COFF machine: 0x%04X",machine));
                if (machine==0xaa64) out.append(" (ARM64 or ARM64X carrier)");
                else if (machine==0xa641) out.append(" (ARM64EC)");
                else out.append(" (other)");
                out.append("; optional header: ").append(magic==0x20b?"PE32+":"PE32").append('\n');
                long sect=optional+optionalBytes;
                List<long[]> parts=new ArrayList<>();
                for (int i=0;i<sectionsCount;i++) {
                    long at=sect+40L*i;
                    long virtualSize=u32(f,at+8);
                    long va=u32(f,at+12);
                    long rawSize=u32(f,at+16);
                    long rawOffset=u32(f,at+20);
                    if (rawOffset>f.length() || rawSize>f.length()-rawOffset)
                        throw new SecurityException("Unsafe PE section raw bounds");
                    parts.add(new long[]{va,Math.max(virtualSize,rawSize),rawSize,rawOffset});
                }
                long importEntry=optional+(magic==0x20b?112:96)+8;
                if (importEntry+8>optional+optionalBytes) {
                    out.append("Import data directory absent\n");
                    return out.toString();
                }
                long rva=u32(f,importEntry), size=u32(f,importEntry+4);
                if (rva==0 || size==0) {
                    out.append("Direct PE import descriptors: 0\n");
                    return out.toString();
                }
                long desc=map(rva,parts);
                if (desc<0 || desc>f.length()-20)
                    throw new SecurityException("Unmapped PE import directory");
                TreeSet<String> imports=new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
                int seen=0;
                for (;seen<64;seen++) {
                    long at=desc+20L*seen;
                    if (at+20>f.length()) throw new SecurityException("Truncated PE imports");
                    long first=u32(f,at), time=u32(f,at+4);
                    long forward=u32(f,at+8), name=u32(f,at+12);
                    long thunk=u32(f,at+16);
                    if ((first|time|forward|name|thunk)==0) break;
                    long nameOffset=map(name,parts);
                    if (nameOffset<0) throw new SecurityException("Unmapped import name");
                    imports.add(ascii(f,nameOffset));
                }
                if (seen==64) out.append("Import descriptors truncated at 64\n");
                out.append("Direct PE DLL import names (").append(imports.size())
                   .append("):\n");
                int shown=0;
                for (String imp:imports) {
                    if (shown++==40) { out.append("  [remaining names omitted]\n"); break; }
                    File hybrid=new File(arm64ecDir,imp.toLowerCase(Locale.US));
                    File regular=new File(arm64Dir,imp.toLowerCase(Locale.US));
                    // existence only; never open a symlink or consult Android system directories
                    boolean h=hybrid.isFile() && hybrid.getCanonicalFile().equals(hybrid.getAbsoluteFile());
                    boolean a=regular.isFile() && regular.getCanonicalFile().equals(regular.getAbsoluteFile());
                    out.append("  ").append(imp).append(": ");
                    if (h) out.append("staged arm64ec/ARM64X");
                    if (a) out.append(h?" + staged ARM64":"staged ARM64");
                    if (!h && !a) out.append("not in this 23-PE scratch cohort");
                    out.append('\n');
                }
            }
        } catch (Exception ex) {
            out.append("RESULT: BLOCKED — malformed or inaccessible PE: ")
               .append(ex.getClass().getSimpleName()).append('\n');
        }
        return out.toString();
    }
}
