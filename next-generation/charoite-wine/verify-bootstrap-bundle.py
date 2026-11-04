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
EXTRA_PE=("win32u","gdi32","ucrtbase","shell32")
COM_PE=("rpcrt4","combase","ole32","comctl32")
SERVICES_PE=("bcrypt","secur32","sechost","msvcrt")
APISET_PATH={"apisetschema":"runtime/pe/arm64ec/apisetschema.dll"}
APISET_SOURCES=("apisetschema.spec","apisetschema.Makefile.in","apisetschema-verified.json")
WINE29_SOURCES=("charoite-wine29-native-source-delta.patch",
                "charoite-wine29-native-source-validation.json")
WINE29_VERSION="wine10-arm64ec-bootstrap.0.7"
WINE29_MARKERS={
    "wine":(b"CHAROITE_WINE29_NATIVE_DIR",b"libcharoite_wine29_ntdll.so"),
    "wineserver":(b"CHAROITE_WINE29_DATA_DIR",b"Wine29/Wine28 selector conflict"),
    "ntdll_unix":(b"CHAROITE_WINE29_PE_DIR",b"CHAROITE_WINE29_DATA_DIR",
                  b"apisetschema.dll"),
}
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
EXTRA_PATHS={k:f"runtime/pe/arm64ec/{k}.dll" for k in EXTRA_PE}
COM_PATHS={k:f"runtime/pe/arm64ec/{k}.dll" for k in COM_PE}
SERVICES_PATHS={k:f"runtime/pe/arm64ec/{k}.dll" for k in SERVICES_PE}
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
        version=manifest.get("version")
        wine29=version==WINE29_VERSION
        extended=version in ("wine10-arm64ec-bootstrap.0.3","wine10-arm64ec-bootstrap.0.4","wine10-arm64ec-bootstrap.0.5","wine10-arm64ec-bootstrap.0.6",WINE29_VERSION)
        com=version in ("wine10-arm64ec-bootstrap.0.4","wine10-arm64ec-bootstrap.0.5","wine10-arm64ec-bootstrap.0.6",WINE29_VERSION)
        services=version in ("wine10-arm64ec-bootstrap.0.5","wine10-arm64ec-bootstrap.0.6",WINE29_VERSION)
        apiset=version in ("wine10-arm64ec-bootstrap.0.6",WINE29_VERSION)
        source_names=set(SOURCES) | (set(APISET_SOURCES) if apiset else set()) | (
            set(WINE29_SOURCES) if wine29 else set())
        expected={**EXPECTED,**(EXTRA_PATHS if extended else {}),
                  **(COM_PATHS if com else {}),
                  **(SERVICES_PATHS if services else {}),
                  **(APISET_PATH if apiset else {})}
        allowed=ALL | (set(EXTRA_PATHS.values()) if extended else set()) | (
            set(COM_PATHS.values()) if com else set()) | (
            set(SERVICES_PATHS.values()) if services else set()) | (
            set(APISET_PATH.values()) if apiset else set()) | {
            "source/"+name for name in APISET_SOURCES if apiset} | {
            "source/"+name for name in WINE29_SOURCES if wine29}
        if (len(members)!=len(allowed)+len(nls_paths) or actual!=allowed|nls_paths):
            raise ValueError("Wrong, repeated or missing bundle files")
        if (manifest.get("schema_version")!=1 or
            manifest.get("version") not in (
                "wine10-arm64ec-bootstrap.0.2","wine10-arm64ec-bootstrap.0.3",
                "wine10-arm64ec-bootstrap.0.4",
                "wine10-arm64ec-bootstrap.0.5",
                "wine10-arm64ec-bootstrap.0.6",WINE29_VERSION) or
            manifest.get("source_commit")!=BASE or
            manifest.get("android_package")!="com.charoitx" or
            manifest.get("status")!="coherent-components-not-executed" or
            manifest.get("component_count")!=len(expected) or
            any(manifest.get(x) is not False for x in (
                "launch_ready","installable","prefix_created","device_tested",
                "anti_cheat_supported")) or
            manifest.get("dependency_review_sha256")!=digest(report_raw) or
            set(manifest.get("components",{}))!=set(expected) or
            set(manifest.get("source_files",{}))!=source_names):
            raise ValueError("Unsafe/incomplete bootstrap manifest")
        nls_files=manifest.get("nls_files")
        if (not isinstance(nls_files,dict) or len(nls_files)!=76 or
            manifest.get("nls_count")!=76 or
            not NLS_REQUIRED.issubset(nls_files) or
            nls_paths!={"runtime/nls/"+name for name in nls_files}):
            raise ValueError("Missing or unexpected Wine NLS tables")
        startup_hash=manifest.get("startup_dependency_manifest_sha256")
        if extended:
            if not isinstance(startup_hash,str) or not re.fullmatch(r"[0-9a-f]{64}",startup_hash):
                raise ValueError("Missing startup DLL source audit linkage")
        elif startup_hash is not None:
            raise ValueError("Unexpected startup provenance in base archive")
        com_hash=manifest.get("com_dependency_manifest_sha256")
        if com:
            if not isinstance(com_hash,str) or not re.fullmatch(r"[0-9a-f]{64}",com_hash):
                raise ValueError("Missing COM/RPC source provenance")
        elif com_hash is not None:
            raise ValueError("Unexpected COM/RPC provenance in older archive")
        services_hash=manifest.get("services_dependency_manifest_sha256")
        if services:
            if not isinstance(services_hash,str) or not re.fullmatch(r"[0-9a-f]{64}",services_hash):
                raise ValueError("Missing source-verified PE security/service manifest")
        elif services_hash is not None:
            raise ValueError("Unexpected PE services provenance on older bundle")
        apiset_source_hash=manifest.get("api_set_source_manifest_sha256")
        if apiset:
            if not isinstance(apiset_source_hash,str) or not re.fullmatch(r"[0-9a-f]{64}",apiset_source_hash):
                raise ValueError("Missing API-set source-proof hash")
        elif apiset_source_hash is not None:
            raise ValueError("Unexpected API-set source proof on older generation")
        for name,path in expected.items():
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
                elif name=="apisetschema":
                    if (machine not in (0xAA64,0xA641) or
                        entry.get("machine")!=f"0x{machine:04X}" or
                        entry.get("api_set_namespace_version")!=6):
                        raise ValueError("Windows API-set source ABI report invalid")
                elif machine not in (0xAA64,0xA641) or entry.get("machine")!="0xA641":
                    raise ValueError("Windows DLL missing ARM64EC ABI report")
                if not isinstance(entry.get("imports"),list):
                    raise ValueError("Missing PE imports audit")
        for name in sorted(source_names):
            entry=manifest["source_files"][name]
            data=read("source/"+name)
            if (entry.get("path")!="source/"+name or entry.get("size")!=len(data) or
                entry.get("sha256")!=digest(data)):
                raise ValueError("Corresponding Wine source/license tampered")
        if apiset:
            delta=read("source/charoite-source-delta.patch")
            if (b"CHAROITE_WINE28_PE_DIR" not in delta or
                b"verified isolated Wine28 API-set PE is absent or unreadable" not in delta):
                raise ValueError("API-set native loader source patch absent")
            import importlib.util
            verify_path=Path(__file__).resolve().parent/"verify-apiset-bootstrap.py"
            spec=importlib.util.spec_from_file_location("charoite_apiset_verifier",verify_path)
            helper=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            module_data=read(APISET_PATH["apisetschema"])
            namespace=helper.inspect(module_data)
            proof_raw=read("source/apisetschema-verified.json")
            proof=json.loads(proof_raw)
            if (digest(proof_raw)!=apiset_source_hash or
                proof.get("source_commit")!=BASE or
                proof.get("package")!="com.charoitx" or
                proof.get("module")!=namespace or
                proof.get("spec_sha256")!=digest(read("source/apisetschema.spec")) or
                proof.get("make_sha256")!=digest(read("source/apisetschema.Makefile.in"))):
                raise ValueError("Source-coherent API-set proof mismatch")
        if wine29:
            raw_proof=read("source/charoite-wine29-native-source-validation.json")
            raw_delta=read("source/charoite-wine29-native-source-delta.patch")
            proof=json.loads(raw_proof)
            if (manifest.get("wine29_native_source_proof_sha256")!=digest(raw_proof) or
                manifest.get("wine29_native_source_delta_sha256")!=digest(raw_delta) or
                proof.get("generation")!=WINE29_VERSION or
                proof.get("source_commit")!=BASE or
                proof.get("package")!="com.charoitx" or
                proof.get("delta_sha256")!=digest(raw_delta) or
                set(proof.get("patch_sources",{}))!={
                    "loader/main.c","dlls/ntdll/unix/loader.c","server/unicode.c"} or
                any(proof.get(k) is not False for k in
                    ("runtime_executable","device_tested","native_elf_installed",
                     "legacy_wine28_cohort_modified"))):
                raise ValueError("Invalid independent Wine29 native source-generation proof")
            for item in proof["patch_sources"].values():
                if (not isinstance(item,dict) or
                    not isinstance(item.get("before_sha256"),str) or
                    not isinstance(item.get("after_sha256"),str) or
                    not re.fullmatch("[0-9a-f]{64}",item["before_sha256"]) or
                    not re.fullmatch("[0-9a-f]{64}",item["after_sha256"]) or
                    item["before_sha256"]==item["after_sha256"]):
                    raise ValueError("Invalid Wine29 patched source hashes")
            for marker in (b"CHAROITE_WINE29_NATIVE_DIR",b"CHAROITE_WINE29_PE_DIR",
                           b"CHAROITE_WINE29_DATA_DIR",b"Wine29/Wine28 selector conflict",
                           b"libcharoite_wine29_ntdll.so"):
                if marker not in raw_delta:
                    raise ValueError("Wine29 native selector patch absent")
            for name,markers in WINE29_MARKERS.items():
                payload=read(EXPECTED[name])
                if any(marker not in payload for marker in markers):
                    raise ValueError("Actual Wine29 native ELF missing generation-specific selectors: "+name)
        elif ("wine29_native_source_proof_sha256" in manifest or
              "wine29_native_source_delta_sha256" in manifest):
            raise ValueError("Earlier Wine archive falsely claims Wine29 native source")
        for name,entry in nls_files.items():
            if not re.fullmatch(r"[a-z_0-9]+\.nls",name):
                raise ValueError("Unsafe NLS file name")
            path="runtime/nls/"+name
            data=read(path)
            if (entry.get("path")!=path or entry.get("size")!=len(data) or
                entry.get("sha256")!=digest(data)):
                raise ValueError("Wine NLS file hash or size mismatch")
        imports={dll for info in manifest["components"].values() for dll in info.get("imports",[])}
        needed={dll for info in manifest["components"].values() for dll in info.get("needed",[])}
        bundled={name+".dll" for name in expected if name not in ELF and name!="wineboot"}
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
