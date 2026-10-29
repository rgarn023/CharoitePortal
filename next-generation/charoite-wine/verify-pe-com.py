#!/usr/bin/env python3
"""Read-only integrity, hybrid PE ABI and import-audit check for COM/RPC DLLs."""
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import sys

SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
NAMES = ("rpcrt4", "combase", "ole32", "comctl32")
PURPOSE = "Exact imports in sampled compiled bootstrap; not full runtime dependency closure"

def bytes_of(p):
    p=Path(p)
    info=p.lstat()
    if p.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size<=0:
        raise ValueError("Unsafe or missing COM/RPC file")
    return p.read_bytes()

def verify(root, audit):
    root=Path(root)
    evidence=bytes_of(audit)
    report=json.loads(evidence)
    if (report.get("schema_version")!=1 or report.get("purpose")!=PURPOSE or
        not {n+".dll" for n in NAMES}.issubset(
            set(report.get("windows_imports_not_bundled",[])))):
        raise ValueError("COM/RPC source audit did not contain requested imports")
    manifest=json.loads(bytes_of(root/"pe-com-manifest.json"))
    if (manifest.get("schema_version")!=1 or
        manifest.get("source_commit")!=SOURCE or
        manifest.get("android_package")!="com.charoitx" or
        manifest.get("status")!="compiled-not-executed" or
        manifest.get("dependency_review_sha256")!=hashlib.sha256(evidence).hexdigest() or
        any(manifest.get(k) is not False for k in
            ("launch_ready","installable","prefix_created","device_tested","anti_cheat_supported")) or
        set(manifest.get("components",{}))!=set(NAMES)):
        raise ValueError("Unsafe COM/RPC module manifest")
    expected={"pe-com-manifest.json"}
    for name in NAMES:
        binary_name=f"{name}-arm64ec.dll"
        header_name=f"{name}-pe-header.txt"
        import_name=f"{name}-pe-imports.txt"
        expected.update((binary_name,header_name,import_name))
        record=manifest["components"][name]
        if (record.get("file")!=binary_name or record.get("pe_machine")!="0xA641" or
            record.get("raw_arm64x_carrier")!="0xAA64"):
            raise ValueError("COM/RPC ABI mismatch in manifest")
        data=bytes_of(root/binary_name)
        if record.get("size")!=len(data) or record.get("sha256")!=hashlib.sha256(data).hexdigest():
            raise ValueError("COM/RPC binary SHA or size mismatch")
        if len(data)<64 or data[:2]!=b"MZ": raise ValueError("Invalid PE DOS header")
        pe=struct.unpack_from("<I",data,0x3c)[0]
        if pe+6>len(data) or data[pe:pe+4]!=b"PE\x00\x00":
            raise ValueError("COM/RPC PE signature missing")
        if struct.unpack_from("<H",data,pe+4)[0]!=0xAA64:
            raise ValueError("COM/RPC PE ARM64X carrier required")
        header=bytes_of(root/header_name).decode("utf-8")
        for token in ("Format: COFF-ARM64X",
                      "Machine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)",
                      "Format: COFF-ARM64EC",
                      "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)"):
            if token not in header:
                raise ValueError("COM/RPC PE ARM64EC dual view missing")
        imports=bytes_of(root/import_name).decode("utf-8")
        if "File:" not in imports or "Format:" not in imports:
            raise ValueError("COM/RPC missing import inspector report")
    if {p.name for p in root.iterdir()}!=expected:
        raise ValueError("Unexpected COM/RPC files in experiment")
    return manifest

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: verify-pe-com.py ABS_BUNDLE ABS_18_REVIEW")
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print("CHAROITE_PE_COM_MANIFEST_VERIFIED=PASS")
    print("LAUNCH_READY=false")
