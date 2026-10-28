#!/usr/bin/env python3
"""No-install SHA-256 and ARM64X/ARM64EC verification of expanded Wine PE DLLs."""
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import sys

SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
NAMES=("crypt32","setupapi","shlwapi","version")
DUAL_VIEW=(
    r"Format:\s+COFF-ARM64X",
    r"Machine:\s+IMAGE_FILE_MACHINE_ARM64X\s+\(0xA64E\)",
    r"Format:\s+COFF-ARM64EC",
    r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)",
)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_regular(path):
    path=Path(path)
    info=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or not info.st_size:
        raise ValueError("Missing or unsafe regular file")
    return path.read_bytes()

def raw_machine(data):
    if len(data)<0x40 or data[:2]!=b"MZ":
        raise ValueError("Missing PE DOS header")
    offset=struct.unpack_from("<I",data,0x3c)[0]
    if offset+6>len(data) or data[offset:offset+4]!=b"PE\x00\x00":
        raise ValueError("Missing PE signature")
    return struct.unpack_from("<H",data,offset+4)[0]

def verify(root, foundation):
    root=Path(root); foundation=Path(foundation)
    # The foundation itself must be valid, not merely a plausible manifest hash.
    import importlib.util
    spec=importlib.util.spec_from_file_location(
        "charoite_foundation_verifier",Path(__file__).resolve().parent/"verify-pe-foundation.py")
    fv=importlib.util.module_from_spec(spec);spec.loader.exec_module(fv)
    fv.verify(foundation)
    raw_manifest=read_regular(root/"pe-expansion-manifest.json")
    m=json.loads(raw_manifest)
    if (m.get("schema_version")!=1 or m.get("source_commit")!=SOURCE or
        m.get("android_package")!="com.charoitx" or
        m.get("status")!="compiled-not-executed" or
        any(m.get(k) is not False for k in (
            "launch_ready","installable","prefix_created","device_tested","anti_cheat_supported")) or
        m.get("depends_on_foundation_manifest_sha256")!=sha256(
            foundation/"pe-foundation-manifest.json") or
        set(m.get("components",{}))!=set(NAMES)):
        raise ValueError("Unsafe or incomplete PE expansion manifest")
    expected={"pe-expansion-manifest.json"}
    for name in NAMES:
        filename=f"{name}-arm64ec.dll"; report=f"{name}-pe-header.txt"
        expected.update((filename,report))
        entry=m["components"][name]
        if (entry.get("file")!=filename or entry.get("pe_machine")!="0xA641" or
            entry.get("raw_arm64x_carrier")!="0xAA64"):
            raise ValueError("PE expansion component identity mismatch")
        data=read_regular(root/filename)
        if len(data)!=entry.get("size") or hashlib.sha256(data).hexdigest()!=entry.get("sha256"):
            raise ValueError("PE expansion hash mismatch")
        if raw_machine(data)!=0xAA64:
            raise ValueError("PE expansion is not ARM64X carrier")
        header=read_regular(root/report).decode("utf-8")
        if not all(re.search(pattern,header) for pattern in DUAL_VIEW):
            raise ValueError("Missing ARM64X and ARM64EC dual-view report")
    if {p.name for p in root.iterdir()}!=expected:
        raise ValueError("Unexpected PE expansion files")
    return m

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: verify-pe-expansion.py DIR FOUNDATION_DIR")
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print("CHAROITE_PE_EXPANSION_ABI=PASS")
    print("CHAROITE_PE_EXPANSION_MANIFEST_VERIFIED=PASS")
    print("LAUNCH_READY=false")
