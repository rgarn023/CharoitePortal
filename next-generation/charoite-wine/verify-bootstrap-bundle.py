#!/usr/bin/env python3
"""Read-only verification of a coherent but NON-RUNNABLE Charoite Wine bundle."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import struct
import sys
import tarfile

BASE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
ELF=("wine","wineserver","ntdll_unix")
PE=("ntdll","kernelbase","kernel32","advapi32","user32","ws2_32",
    "crypt32","setupapi","shlwapi","version","wineboot")
SOURCES=("COPYING.LIB","LICENSE","charoite-source-delta.patch","WEHAVEPHONES-MIT.txt",
         "Wine-NLS-Makefile.in")
NLS_REQUIRED={"c_932.nls","c_1252.nls","l_intl.nls","locale.nls","sortdefault.nls"}
EXPECTED={
    "wine":"runtime/bin/wine",
    "wineserver":"runtime/bin/wineserver",
    "ntdll_unix":"runtime/lib/ntdll.so",
    **{k:f"runtime/pe/arm64ec/{k}.dll" for k in PE if k!="wineboot"},
    "wineboot":"runtime/pe/arm64/wineboot.exe",
}
ALL=set(EXPECTED.values())|{f"source/{k}" for k in SOURCES}|{
    "dependency-review.json","manifest.json",
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def pe_raw_machine(data: bytes) -> int:
    if len(data)<64 or data[:2]!=b"MZ": raise ValueError("Missing PE DOS header")
    offset=struct.unpack_from("<I",data,0x3c)[0]
    if offset+6>len(data) or data[offset:offset+4]!=b"PE\x00\x00":
        raise ValueError("PE signature missing")
    return struct.unpack_from("<H",data,offset+4)[0]

def elf_machine(data: bytes) -> int:
    if len(data)<20 or data[:6]!=b"\x7fELF\x02\x01":
        raise ValueError("Expected little-endian 64-bit ELF")
    return struct.unpack_from("<H",data,18)[0]

def verify(archive: Path) -> tuple[dict,dict]:
    if archive.is_symlink() or not archive.is_file(): raise ValueError("No regular archive")
    with tarfile.open(archive,"r:gz") as tar:
        members=tar.getmembers()
        actual={m.name for m in members}
        nls_paths={name for name in actual if name.startswith("runtime/nls/")}
        if (len(members)!=len(ALL)+len(nls_paths) or
            actual!=ALL|nls_paths):
            raise ValueError("Wrong, repeated or missing bundle files")
        for m in members:
            path=PurePosixPath(m.name)
            if (not m.isfile() or m.name.startswith("/") or ".." in path.parts or
                m.size<=0 or m.size>256*1024*1024):
                raise ValueError("Unsafe archive member")
        def read(name):
            with tar.extractfile(name) as f: return f.read()
        manifest=json.loads(read("manifest.json"))
        report_raw=read("dependency-review.json")
        report=json.loads(report_raw)
        if (manifest.get("schema_version")!=1 or
            manifest.get("version")!="wine10-arm64ec-bootstrap.0.2" or
            manifest.get("source_commit")!=BASE or
            manifest.get("android_package")!="com.charoitx" or
            manifest.get("status")!="coherent-components-not-executed" or
            manifest.get("component_count")!=len(EXPECTED) or
            any(manifest.get(x) is not False for x in (
                "launch_ready","installable","prefix_created","device_tested",
                "anti_cheat_supported")) or
            manifest.get("dependency_review_sha256")!=digest(report_raw) or
            set(manifest.get("components",{}))!=set(EXPECTED) or
            set(manifest.get("source_files",{}))!=set(SOURCES)):
            raise ValueError("Unsafe/incomplete bootstrap manifest")
        nls_files=manifest.get("nls_files")
        if (not isinstance(nls_files,dict) or len(nls_files)!=76 or
            manifest.get("nls_count")!=76 or
            not NLS_REQUIRED.issubset(nls_files) or
            nls_paths!={"runtime/nls/"+name for name in nls_files}):
            raise ValueError("Missing or unexpected Wine NLS tables")
        for name,path in EXPECTED.items():
            entry=manifest["components"][name]
            if entry.get("path")!=path or entry.get("format")!=(
                "ELF" if name in ELF else "PE"):
                raise ValueError("Component path or format mismatch")
            data=read(path)
            if entry.get("size")!=len(data) or entry.get("sha256")!=digest(data):
                raise ValueError("Component SHA-256/size mismatch")
            if name in ELF:
                if elf_machine(data)!=183 or entry.get("machine")!="AArch64":
                    raise ValueError("Not Android AArch64 ELF")
                align=entry.get("load_alignments")
                if not isinstance(align,list) or not align or any(
                    not isinstance(x,int) or x<16384 for x in align):
                    raise ValueError("Insufficient Android ELF page alignment")
                if not isinstance(entry.get("needed"),list):
                    raise ValueError("Missing native dependency audit")
            else:
                machine=pe_raw_machine(data)
                if name=="wineboot":
                    if machine!=0xAA64 or entry.get("machine")!="0xAA64":
                        raise ValueError("Windows wineboot not regular ARM64")
                elif machine not in (0xAA64,0xA641) or entry.get("machine")!="0xA641":
                    raise ValueError("Windows DLL missing ARM64EC ABI report")
                if not isinstance(entry.get("imports"),list):
                    raise ValueError("Missing PE imports audit")
        for name in SOURCES:
            entry=manifest["source_files"][name]
            data=read("source/"+name)
            if (entry.get("path")!="source/"+name or entry.get("size")!=len(data) or
                entry.get("sha256")!=digest(data)):
                raise ValueError("Corresponding Wine source/license tampered")
        for name,entry in nls_files.items():
            if not re.fullmatch(r"[a-z_0-9]+\\.nls",name):
                raise ValueError("Unsafe NLS file name")
            path="runtime/nls/"+name
            data=read(path)
            if (entry.get("path")!=path or entry.get("size")!=len(data) or
                entry.get("sha256")!=digest(data)):
                raise ValueError("Wine NLS file hash or size mismatch")
        imports={dll for info in manifest["components"].values() for dll in info.get("imports",[])}
        needed={dll for info in manifest["components"].values() for dll in info.get("needed",[])}
        bundled={name+".dll" for name in PE if name!="wineboot"}
        gap=sorted(imports-bundled)
        if (report.get("schema_version")!=1 or report.get("bundled_windows_dlls")!=sorted(bundled)
            or report.get("observed_windows_imports")!=sorted(imports)
            or report.get("windows_imports_not_bundled")!=gap
            or report.get("android_elf_needed")!=sorted(needed)
            or manifest.get("window_imports_unresolved_count")!=len(gap)):
            raise ValueError("Dependency closure report inconsistent with audited imports")
    return manifest,report

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: verify-bootstrap-bundle.py ARCHIVE")
    m,r=verify(Path(sys.argv[1]))
    print("CHAROITE_WINE_BOOTSTRAP_ARCHIVE_VERIFIED=PASS")
    print("COMPONENTS="+str(m["component_count"]))
    print("NLS_COUNT="+str(m["nls_count"]))
    print("PE_IMPORTS_NOT_BUNDLED="+",".join(r["windows_imports_not_bundled"]))
    print("LAUNCH_READY=false")
