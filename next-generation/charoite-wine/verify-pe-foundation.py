#!/usr/bin/env python3
"""Read-only ABI and SHA-256 verification of ARM64EC PE foundation DLLs."""
import hashlib,json,re,stat,struct,sys
from pathlib import Path
SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
NAMES=("advapi32","user32","ws2_32")
def machine_from_file(data):
    if len(data)<0x40 or data[:2]!=b"MZ": raise ValueError("PE DOS header invalid")
    offset=struct.unpack_from("<I",data,0x3c)[0]
    if offset+6>len(data) or data[offset:offset+4]!=b"PE\x00\x00":
        raise ValueError("PE signature invalid")
    return struct.unpack_from("<H",data,offset+4)[0]
def verify(root):
    root=Path(root); marker=root/"pe-foundation-manifest.json"
    if marker.is_symlink() or not marker.is_file(): raise ValueError("Unsafe manifest")
    m=json.loads(marker.read_text(encoding="utf-8"))
    if (m.get("schema_version")!=1 or m.get("source_commit")!=SOURCE or
        m.get("android_package")!="com.charoitx" or
        m.get("status")!="compile-verified-not-executed" or
        any(m.get(k) is not False for k in ("launch_ready","installable","prefix_created","device_tested")) or
        set(m.get("components",{}))!=set(NAMES)):
        raise ValueError("Unsafe or incomplete PE foundation manifest")
    expected={"pe-foundation-manifest.json"}
    for name in NAMES:
        expected|={f"{name}-arm64ec.dll",f"{name}-pe-header.txt"}
        entry=m["components"][name]
        if entry.get("file")!=f"{name}-arm64ec.dll" or entry.get("pe_machine")!="0xA641":
            raise ValueError("Wrong component identity")
        path=root/entry["file"]
        st=path.lstat()
        if not stat.S_ISREG(st.st_mode) or path.is_symlink() or st.st_size==0:
            raise ValueError("Missing or unsafe PE DLL")
        data=path.read_bytes()
        if len(data)!=entry.get("size") or hashlib.sha256(data).hexdigest()!=entry.get("sha256"):
            raise ValueError("PE DLL digest mismatch")
        # Wine's -marm64x DLL is an ARM64 loader carrier with a second ARM64EC view.
        # A raw AA64 COFF value is expected; the LLVM report must prove both
        # ARM64X and ARM64EC views. Never mistake plain ARM64 for the hybrid DLL.
        if machine_from_file(data)!=0xAA64:
            raise ValueError("PE DLL is not an ARM64X carrier (raw AA64)")
        report=root/f"{name}-pe-header.txt"
        if report.is_symlink() or not report.is_file():
            raise ValueError("Missing PE inspection report")
        header=report.read_text(encoding="utf-8")
        if not all(re.search(pattern,header) for pattern in (
            r"Format:\s+COFF-ARM64X",
            r"Machine:\s+IMAGE_FILE_MACHINE_ARM64X\s+\(0xA64E\)",
            r"Format:\s+COFF-ARM64EC",
            r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)",
        )):
            raise ValueError("PE inspection report lacks ARM64X/ARM64EC dual view")
    if {p.name for p in root.iterdir()}!=expected: raise ValueError("Unexpected bundle entries")
    return m
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: verify-pe-foundation.py DIR")
    verify(Path(sys.argv[1]))
    print("CHAROITE_PE_FOUNDATION_ABI=PASS")
    print("CHAROITE_PE_FOUNDATION_MANIFEST_VERIFIED=PASS")
    print("LAUNCH_READY=false")
