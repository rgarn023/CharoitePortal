#!/usr/bin/env python3
"""Verify pinned source-built ARM64EC security/service/CRT modules; never run code."""
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import sys

SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
NAMES=("bcrypt","secur32","sechost","msvcrt")
PURPOSE="Exact imports in sampled compiled bootstrap; not full runtime dependency closure"

def blob(path):
    path=Path(path)
    st=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(st.st_mode) or not 0 < st.st_size <= 64*1024*1024:
        raise ValueError("Unsafe or missing module source")
    return path.read_bytes()

def verify(root, review):
    root=Path(root)
    raw_review=blob(review)
    audit=json.loads(raw_review)
    expected_dlls={n+".dll" for n in NAMES}
    if audit.get("schema_version")!=1 or audit.get("purpose")!=PURPOSE or (
        not expected_dlls.issubset(set(audit.get("windows_imports_not_bundled",[])))):
        raise ValueError("Source dependency review missing security/runtime imports")
    manifest=json.loads(blob(root/"pe-services-manifest.json"))
    if (manifest.get("schema_version")!=1 or
        manifest.get("source_commit")!=SOURCE or
        manifest.get("android_package")!="com.charoitx" or
        manifest.get("status")!="compiled-not-executed" or
        manifest.get("dependency_review_sha256")!=hashlib.sha256(raw_review).hexdigest() or
        any(manifest.get(k) is not False for k in (
            "launch_ready","installable","prefix_created","device_tested",
            "anti_cheat_supported")) or
        set(manifest.get("components",{}))!=set(NAMES)):
        raise ValueError("Unverified services source attribution or unsafe readiness claim")
    expected={"pe-services-manifest.json"}
    for name in NAMES:
        binary=f"{name}-arm64ec.dll"
        header=f"{name}-pe-header.txt"
        imports=f"{name}-pe-imports.txt"
        expected.update((binary,header,imports))
        entry=manifest["components"][name]
        raw=blob(root/binary)
        if entry.get("file")!=binary or entry.get("pe_machine")!="0xA641" or (
            entry.get("raw_arm64x_carrier")!="0xAA64" or
            entry.get("size")!=len(raw) or
            entry.get("sha256")!=hashlib.sha256(raw).hexdigest()):
            raise ValueError("PE services binary hash or ABI manifest mismatch")
        if len(raw)<64 or raw[:2]!=b"MZ":
            raise ValueError("PE header missing")
        offset=struct.unpack_from("<I",raw,60)[0]
        if offset+6>len(raw) or raw[offset:offset+4]!=b"PE\x00\x00" or (
            struct.unpack_from("<H",raw,offset+4)[0]!=0xAA64):
            raise ValueError("ARM64X carrier absent")
        text=blob(root/header).decode("utf-8")
        for token in ("Format: COFF-ARM64X",
                      "Machine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)",
                      "Format: COFF-ARM64EC",
                      "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)"):
            if token not in text:
                raise ValueError("Missing dual ARM64X/ARM64EC views")
        import_text=blob(root/imports).decode("utf-8")
        if "File:" not in import_text or "Format:" not in import_text:
            raise ValueError("No audited Windows PE import symbols")
    if {p.name for p in root.iterdir()}!=expected:
        raise ValueError("Unexpected source-built PE services output files")
    return manifest

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: verify-pe-services.py ABS_OUTPUT ABS_22_REVIEW")
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print("CHAROITE_PE_SERVICES_MANIFEST_VERIFIED=PASS")
    print("LAUNCH_READY=false")
