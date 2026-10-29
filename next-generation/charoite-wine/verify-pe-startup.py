#!/usr/bin/env python3
"""Fail-closed verification of source-built ARM64X / ARM64EC startup DLLs."""
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import sys

SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
NAMES=("win32u","gdi32","ucrtbase","shell32")
DUAL=(
    r"Format:\s+COFF-ARM64X",
    r"Machine:\s+IMAGE_FILE_MACHINE_ARM64X\s+\(0xA64E\)",
    r"Format:\s+COFF-ARM64EC",
    r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)",
)

def regular(path):
    p=Path(path)
    info=p.lstat()
    if p.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size<=0:
        raise ValueError("Unsafe or empty startup input")
    return p.read_bytes()

def machine(data):
    if len(data)<64 or data[:2]!=b"MZ": raise ValueError("Missing DOS header")
    pe=struct.unpack_from("<I",data,0x3c)[0]
    if pe+6>len(data) or data[pe:pe+4]!=b"PE\x00\x00":
        raise ValueError("Invalid PE signature")
    return struct.unpack_from("<H",data,pe+4)[0]

def verify(root, base_review):
    root=Path(root)
    base=json.loads(regular(base_review))
    expected_base={"win32u.dll","gdi32.dll","ucrtbase.dll","shell32.dll"}
    if (base.get("schema_version")!=1 or
        base.get("purpose")!="Exact imports in sampled compiled bootstrap; not full runtime dependency closure" or
        not expected_base.issubset(set(base.get("windows_imports_not_bundled",[])))):
        raise ValueError("Invalid earlier bootstrap import evidence")
    blob=regular(root/"pe-startup-manifest.json")
    m=json.loads(blob)
    if (m.get("schema_version")!=1 or m.get("source_commit")!=SOURCE or
        m.get("android_package")!="com.charoitx" or
        m.get("status")!="compiled-not-executed" or
        m.get("base_dependency_review_sha256")!=hashlib.sha256(regular(base_review)).hexdigest() or
        any(m.get(k) is not False for k in (
            "launch_ready","installable","prefix_created","device_tested","anti_cheat_supported")) or
        set(m.get("components",{}))!=set(NAMES)):
        raise ValueError("Unsafe or incomplete PE startup manifest")
    expected_files={"pe-startup-manifest.json"}
    for name in NAMES:
        filename=f"{name}-arm64ec.dll"
        header=f"{name}-pe-header.txt"
        imports=f"{name}-pe-imports.txt"
        expected_files.update((filename,header,imports))
        entry=m["components"][name]
        if (entry.get("file")!=filename or entry.get("pe_machine")!="0xA641" or
            entry.get("raw_arm64x_carrier")!="0xAA64"):
            raise ValueError("Unexpected startup identity")
        data=regular(root/filename)
        if entry.get("size")!=len(data) or entry.get("sha256")!=hashlib.sha256(data).hexdigest():
            raise ValueError("Startup DLL hash mismatch")
        if machine(data)!=0xAA64:
            raise ValueError("Startup DLL not ARM64X carrier")
        report=regular(root/header).decode("utf-8")
        if not all(re.search(expr,report) for expr in DUAL):
            raise ValueError("Missing ARM64X / ARM64EC dual view")
        # A per-DLL import inspection is required even for import-free modules.
        inspection=regular(root/imports).decode("utf-8")
        if "File:" not in inspection or "Format:" not in inspection:
            raise ValueError("Missing valid LLVM import inspection")
    if {p.name for p in root.iterdir()}!=expected_files:
        raise ValueError("Unexpected startup bundle contents")
    return m

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: verify-pe-startup.py DIR DEPENDENCY_REVIEW_JSON")
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print("CHAROITE_PE_STARTUP_ABI=PASS")
    print("CHAROITE_PE_STARTUP_MANIFEST_VERIFIED=PASS")
    print("LAUNCH_READY=false")
