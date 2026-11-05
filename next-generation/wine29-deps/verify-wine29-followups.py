#!/usr/bin/env python3
"""Static Wine29 .0.7 urlmon/windowscodecs source-only PE candidate verifier.

The independent original 27-component pinned archive and earlier six new DLLs
must verify before these two artifacts can be accepted. No Wine/PE execution.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

GENERATION="wine10-arm64ec-dependencies.0.8-followups"
SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
BASELINE_SHA="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
MODULES=("urlmon","windowscodecs")
SIX=("coml2","imm32","oleacc","oleaut32","shcore","newdev")
MAX_SIZE=32*1024*1024
ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def checked_file(path:Path)->bytes:
    info=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_SIZE:
        raise ValueError("Unsafe source candidate file: "+path.name)
    data=path.read_bytes()
    if len(data)!=info.st_size: raise ValueError("File modified during read")
    return data

def module_file(path:Path,name:str,readobj:Path)->dict:
    dll=path/(name+"-arm64ec.dll")
    blob=checked_file(dll)
    local=ROOT/"verify-wine29-deps.py"
    spec=importlib.util.spec_from_file_location("wine29_followup_machine",local)
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    machine=baseline.raw_coff_machine(blob)
    h=checked_file(path/(name+"-pe-header.txt"))
    im=checked_file(path/(name+"-pe-imports.txt"))
    fresh_h=subprocess.run([str(readobj),"--file-headers",str(dll)],
                           check=True,capture_output=True).stdout
    fresh_im=subprocess.run([str(readobj),"--coff-imports",str(dll)],
                            check=True,capture_output=True).stdout
    if h!=fresh_h or im!=fresh_im:
        raise ValueError("LLVM inspection does not match exact copied candidate: "+name)
    if b"Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)" not in h:
        raise ValueError("Missing ARM64EC view: "+name)
    imports=sorted({m.decode("ascii").lower() for m in
        re.findall(rb"^\s*Name:\s*([A-Za-z0-9_.+-]+\.dll)\s*$",im,re.M)})
    return dict(filename=dll.name,bytes=len(blob),sha256=sha(blob),
                arm64ec_view="0xA641",raw_machine=f"0x{machine:04X}",
                header_sha256=sha(h),import_log_sha256=sha(im),imports=imports)

def inspect(output:Path,readobj:Path,six:Path,archive:Path)->dict:
    for folder in (output,six):
        if not folder.is_absolute() or folder.is_symlink() or not folder.is_dir():
            raise ValueError("Missing separate read-only cohort directory")
        if any(s in str(folder) for s in ("/data/user/","/data/data/","/storage/emulated/","/sdcard/")):
            raise ValueError("Refusing Android user storage")
    if not readobj.is_absolute() or not readobj.is_file():
        raise ValueError("Missing exact LLVM architecture/import inspector")
    if not archive.is_absolute() or archive.is_symlink() or not archive.is_file():
        raise ValueError("Missing pinned source archive")
    if sha(archive.read_bytes())!=BASELINE_SHA:
        raise ValueError("Wine29 .0.7 archive changed")
    basefile=PARENT/"charoite-wine/verify-bootstrap-bundle.py"
    spec=importlib.util.spec_from_file_location("wine29_verified_original",basefile)
    vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    manifest,review=vm.verify(archive)
    if (manifest.get("version")!="wine10-arm64ec-bootstrap.0.7"
        or manifest.get("component_count")!=27 or manifest.get("nls_count")!=76):
        raise ValueError("Unverified original 27-component Wine29 source")
    sixfile=ROOT/"verify-wine29-deps.py"
    spec=importlib.util.spec_from_file_location("wine29_verified_six",sixfile)
    sm=importlib.util.module_from_spec(spec);spec.loader.exec_module(sm)
    saved=six/"wine29-07-six-candidates.json"
    old=json.loads(checked_file(saved).decode("utf-8"))
    sm.run("verify",six,readobj)
    if (old.get("generation")!="wine10-arm64ec-dependencies.0.8-candidate"
        or old.get("component_count")!=6 or set(old["components"])!=set(SIX)
        or old["portability_patch_proof_sha256"]!=sha(
            checked_file(six/"portable-currency-proof.json"))):
        raise ValueError("Six candidate provenance or hashes missing")
    components={n:module_file(output,n,readobj) for n in MODULES}
    included={n+".dll" for n in manifest["components"] if n not in (
        "wine","wineserver","ntdll_unix","wineboot")}
    included.update(n+".dll" for n in SIX+MODULES)
    base_imports={dll for item in manifest["components"].values()
                  for dll in item.get("imports",[])}
    six_imports={dll for entry in old["components"].values()
                 for dll in entry["imports"]}
    added_imports={dll for entry in components.values()
                   for dll in entry["imports"]}
    return {
        "schema_version":1,"generation":GENERATION,
        "source_commit":SOURCE,"baseline_archive_sha256":BASELINE_SHA,
        "six_cohort_sha256":sha(checked_file(saved)),
        "six_portable_currency_sha256":old["portability_patch_proof_sha256"],
        "component_count":2,
        "components":components,
        "combined_bundled_dll_count":len(included),
        "combined_source_static_import_names":sorted(base_imports|six_imports|added_imports),
        "combined_source_imports_not_in_31_known_pe_files":
            sorted((base_imports|six_imports|added_imports)-included),
        "two_new_direct_imports":sorted(added_imports),
        "two_new_direct_imports_not_in_31_known_pe_files":sorted(added_imports-included),
        "source_only":True,
        "launch_ready":False,"phone_staged":False,"wineboot_executed":False,
        "windows_executed":False,"prefix_created":False,
        "note":"Source/LLVM import inventory, not proof of loader resolution or runtime functionality."
    }

def run(mode:str,output:Path,readobj:Path,six:Path,archive:Path)->dict:
    if mode not in ("create","verify"): raise ValueError("Unrecognized verification mode")
    result=inspect(output,readobj,six,archive)
    report=output/"wine29-07-two-followups.json"
    if mode=="create":
        if report.exists() or report.is_symlink():raise ValueError("Refusing overwrite of cohort report")
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    else:
        saved=json.loads(checked_file(report).decode("utf-8"))
        if result!=saved:raise ValueError("New two PE modules changed since sealing")
        allow={report.name}
        for n in MODULES:
            allow.update((n+"-arm64ec.dll",n+"-pe-header.txt",n+"-pe-imports.txt"))
        if {f.name for f in output.iterdir()}!=allow:
            raise ValueError("Unexpected files in two-module sealed artifact")
    print("WINE29_TWO_PE_HEADERS_HASHES_AND_IMPORTS=PASS")
    print("WINE29_VERIFIED_BASE_27_PLUS_SIX_PLUS_TWO=PASS")
    print("WINE29_COMBINED_IMPORT_GAPS="+",".join(
        result["combined_source_imports_not_in_31_known_pe_files"]))
    print("WINE29_NEW_TWO_DIRECT_IMPORT_GAPS="+",".join(
        result["two_new_direct_imports_not_in_31_known_pe_files"]))
    print("WINE29_PHONE_AND_WINEBOOT_EXECUTION=NOT_ATTEMPTED")
    return result

if __name__=="__main__":
    if len(sys.argv)!=6:
        raise SystemExit("Usage: verify-wine29-followups.py create|verify ABS_TWO_DIR ABS_LLVM ABS_SIX_DIR ABS_ORIGINAL_ARCHIVE")
    run(sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),Path(sys.argv[5]))
