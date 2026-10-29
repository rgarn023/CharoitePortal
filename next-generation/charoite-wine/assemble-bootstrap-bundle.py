#!/usr/bin/env python3
"""Assemble same-build Wine bootstrap components; never install or execute.

A first *coherent binary inventory* with exact PE/ELF imports and licensing.
This is not a runnable prefix, Android APK, or a completed dependency closure.
"""
from __future__ import annotations
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile

SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
PE = {
    "ntdll": "dlls/ntdll/aarch64-windows/ntdll.dll",
    "kernelbase": "dlls/kernelbase/aarch64-windows/kernelbase.dll",
    "kernel32": "dlls/kernel32/aarch64-windows/kernel32.dll",
    "advapi32": "dlls/advapi32/aarch64-windows/advapi32.dll",
    "user32": "dlls/user32/aarch64-windows/user32.dll",
    "ws2_32": "dlls/ws2_32/aarch64-windows/ws2_32.dll",
    "crypt32": "dlls/crypt32/aarch64-windows/crypt32.dll",
    "setupapi": "dlls/setupapi/aarch64-windows/setupapi.dll",
    "shlwapi": "dlls/shlwapi/aarch64-windows/shlwapi.dll",
    "version": "dlls/version/aarch64-windows/version.dll",
}
ELF = {
    "wine": "loader/wine",
    "wineserver": "server/wineserver",
    "ntdll_unix": "dlls/ntdll/ntdll.so",
}
BOOT = "programs/wineboot/aarch64-windows/wineboot.exe"
SOURCES = {
    "COPYING.LIB": "COPYING.LIB",
    "LICENSE": "LICENSE",
    "charoite-source-delta.patch": "charoite-source-delta.patch",
    "WEHAVEPHONES-MIT.txt": "@vendor-license",
}

def regular(path: Path) -> bytes:
    s = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(s.st_mode) or s.st_size <= 0 or s.st_size > 256*1024*1024:
        raise ValueError("Missing or unsafe regular input: " + str(path))
    return path.read_bytes()

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def run(*argv) -> str:
    return subprocess.run(argv, check=True, text=True, capture_output=True).stdout

def load_validator(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verify_previous(build: Path) -> None:
    root=build.parent
    load_validator("next_foundation","verify-pe-foundation.py").verify(root/"charoite-pe-foundation")
    load_validator("next_expansion","verify-pe-expansion.py").verify(
        root/"charoite-pe-expansion",root/"charoite-pe-foundation")
    load_validator("next_kernel","verify-kernel-bridge.py").verify(root/"charoite-kernel-bridge")
    load_validator("next_wineboot","verify-wineboot.py").verify(root/"charoite-wineboot")
    load_validator("next_slice","verify-runtime-slice.py").verify(
        root/"charoite-wine-arm64ec-base-slice.tar.gz")

def check_elf(path: Path, readelf: Path) -> dict:
    header=run(str(readelf),"-h",str(path))
    if not re.search(r"Machine:\s+AArch64\b",header):
        raise ValueError("Not Android AArch64 ELF")
    phdr=run(str(readelf),"-lW",str(path))
    align=[]
    for line in phdr.splitlines():
        if re.match(r"^\s*LOAD\s",line):
            m=re.search(r"(0x[0-9a-fA-F]+)\s*$",line)
            if not m: raise ValueError("Unparseable ELF segment")
            align.append(int(m.group(1),16))
    if not align or min(align)<16384: raise ValueError("ELF 16KiB alignment failed")
    dyn=run(str(readelf),"-dW",str(path))
    needed=sorted(set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]",dyn)))
    interp=re.search(r"\[Requesting program interpreter:\s*([^\]]+)\]",phdr)
    return {"machine":"AArch64","load_alignments":align,"needed":needed,
            "interpreter":interp.group(1) if interp else None}

def check_pe(path: Path, readobj: Path, architecture: str) -> dict:
    header=run(str(readobj),"--file-headers",str(path))
    # Hybrid Wine ARM64X DLLs report a nested ARM64EC view; raw DOS/COFF
    # header can be AA64 while the ARM64EC view is A641.
    id="0xAA64" if architecture=="arm64" else "0xA641"
    name="ARM64" if architecture=="arm64" else "ARM64EC"
    if not re.search(rf"Machine:\s+(?:IMAGE_FILE_MACHINE_{name}|{name})\s+\({id}\)",header):
        raise ValueError(f"Missing PE {name} view")
    imports=run(str(readobj),"--coff-imports",str(path))
    dlls=sorted(set(m.lower() for m in re.findall(
        r"^\s*Name:\s*([A-Za-z0-9_.+-]+\.dll)\s*$",imports,re.M)))
    return {"machine":id,"imports":dlls}

def make_bundle(build: Path, readelf: Path, readobj: Path, output: Path) -> dict:
    for p in (build,readelf,readobj,output):
        if not p.is_absolute(): raise ValueError("Expected absolute CI-only paths")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("Refusing existing or unsafe output")
    for disallowed in ("/data/data/","/data/user/","/storage/emulated/"):
        if any(disallowed in str(x) for x in (build,output)):
            raise ValueError("Refusing installed Android data path")
    if not (build.parent/"charoite-source-validation.txt").is_file():
        raise ValueError("Missing pinned source validation")
    verify_previous(build)
    payloads={}
    records={}
    for name,rel in ELF.items():
        src=build/rel
        data=regular(src)
        dest={"wine":"runtime/bin/wine","wineserver":"runtime/bin/wineserver",
              "ntdll_unix":"runtime/lib/ntdll.so"}[name]
        payloads[dest]=data
        records[name]={"path":dest,"format":"ELF","sha256":sha(data),"size":len(data),
                       **check_elf(src,readelf)}
    for name,rel in PE.items():
        src=build/rel
        data=regular(src)
        dest=f"runtime/pe/arm64ec/{name}.dll"
        payloads[dest]=data
        records[name]={"path":dest,"format":"PE","sha256":sha(data),"size":len(data),
                       **check_pe(src,readobj,"arm64ec")}
    data=regular(build/BOOT)
    dest="runtime/pe/arm64/wineboot.exe"
    payloads[dest]=data
    records["wineboot"]={"path":dest,"format":"PE","sha256":sha(data),"size":len(data),
                         **check_pe(build/BOOT,readobj,"arm64")}
    # Check actual build outputs match the prior independently audited outputs,
    # never merge visually similar files built from different toolchains.
    prior={
        "ntdll":(build.parent/"charoite-arm64ec-artifact"/"ntdll-arm64ec.dll"),
        "kernelbase":(build.parent/"charoite-kernel-bridge"/"kernelbase-arm64ec.dll"),
        "kernel32":(build.parent/"charoite-kernel-bridge"/"kernel32-arm64ec.dll"),
        "wineboot":(build.parent/"charoite-wineboot"/"wineboot-arm64.exe"),
    }
    for group,names in (("charoite-pe-foundation",("advapi32","user32","ws2_32")),
                        ("charoite-pe-expansion",("crypt32","setupapi","shlwapi","version"))):
        for name in names: prior[name]=build.parent/group/f"{name}-arm64ec.dll"
    for name,path in prior.items():
        if sha(regular(path))!=records[name]["sha256"]:
            raise ValueError("Same-tree Wine binary differs from audited component: "+name)
    source={}
    for name,rel in SOURCES.items():
        src=(Path(__file__).resolve().parent/"UPSTREAM-WEHAVEPHONES-LICENSE.txt"
             if rel=="@vendor-license" else build.parent/rel)
        data=regular(src)
        dest=f"source/{name}"
        payloads[dest]=data
        source[name]={"path":dest,"sha256":sha(data),"size":len(data)}
    available={f"{k}.dll" for k in PE}
    imported={v for e in records.values() for v in e.get("imports",[])}
    needed={v for e in records.values() for v in e.get("needed",[])}
    gap=sorted(imported-available)
    report={
        "schema_version":1,
        "purpose":"Exact imports in sampled compiled bootstrap; not full runtime dependency closure",
        "bundled_windows_dlls":sorted(available),
        "observed_windows_imports":sorted(imported),
        "windows_imports_not_bundled":gap,
        "android_elf_needed":sorted(needed),
        "note":"Some imports may be supplied by Android, Wine-builtins or API-set mapping; do not infer launchability from this inventory.",
    }
    payloads["dependency-review.json"]=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode()
    manifest={
        "schema_version":1,"version":"wine10-arm64ec-bootstrap.0.1",
        "source_commit":SOURCE_SHA,"android_package":"com.charoitx",
        "status":"coherent-components-not-executed",
        "launch_ready":False,"installable":False,"prefix_created":False,
        "device_tested":False,"anti_cheat_supported":False,
        "component_count":len(records),"components":records,
        "source_files":source,"dependency_review_sha256":sha(payloads["dependency-review.json"]),
        "window_imports_unresolved_count":len(gap),
        "missing_for_runtime":[
            "Complete Windows PE/Unix module and NLS closure",
            "FEX x86/x64 translator and ARM64EC bridge",
            "Android graphics/window/input and DXVK/VKD3D",
            "Android isolated runtime setup and new-prefix wineboot smoke test",
        ],
    }
    payloads["manifest.json"]=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()
    output.mkdir()
    archive=output/"charoite-wine-bootstrap-bundle.tar.gz"
    with archive.open("wb") as sink, gzip.GzipFile(fileobj=sink,mode="wb",filename="",mtime=0) as gz:
        with tarfile.open(mode="w",fileobj=gz) as tar:
            for name,data in sorted(payloads.items()):
                t=tarfile.TarInfo(name)
                t.mode=0o755 if name.startswith("runtime/bin/") else 0o644
                t.size=len(data);t.uid=0;t.gid=0;t.mtime=0
                tar.addfile(t,io.BytesIO(data))
    (output/"dependency-review.json").write_bytes(payloads["dependency-review.json"])
    (output/"bundle-report.txt").write_text(
        "CHAROITE_WINE_COHERENT_BOOTSTRAP_ASSEMBLED=PASS\n"
        f"COMPONENTS={len(records)}\n"
        f"WINDOWS_IMPORTS_NOT_BUNDLED={len(gap)}\n"
        f"SHA256={sha(regular(archive))}\n"
        "LAUNCH_READY=false\nINSTALLABLE=false\nPREFIX_CREATED=false\n",encoding="utf-8")
    return manifest

if __name__=="__main__":
    if len(sys.argv)!=5:
        raise SystemExit("Usage: assemble-bootstrap-bundle.py ABS_BUILD ABS_READELF ABS_READOBJ ABS_OUTDIR")
    manifest=make_bundle(*map(Path,sys.argv[1:]))
    print("CHAROITE_WINE_COHERENT_BOOTSTRAP_ASSEMBLED=PASS",manifest["component_count"])
    print("LAUNCH_READY=false")
