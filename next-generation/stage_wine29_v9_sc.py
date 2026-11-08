#!/usr/bin/env python3
"""Stage a source-verified ARM64 Wine29 sc.exe into NEW experimental Next APK assets.
Never execute Wine/Windows PE, touch phone data, or overwrite historical assets.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

SOURCE_REV="c74acb09d51b447f5d5ac56c87608d3ec565a767"
SOURCE_RUN=42426173638
SOURCE_COMMIT="311a141fa255886020c5e2adab643db0e954a07a"
SOURCE_ARTIFACT=13595845868
SOURCE_DIGEST="sha256:f8ac4ddbdca513a07ee15b29101b78203d07cd9094e65357e50b9709887e6c54"
ROOT="charoite-next/wine29-v9-sc"
ASSET=ROOT+"/sc-arm64.exe.bin"
INDEX=ROOT+"/sc-index.json"
FILES={"sc-arm64.exe","sc-manifest.json","sc-pe-header.txt","sc-coff-imports.txt"}
FORBIDDEN=("/data/user/","/data/data/","/storage/emulated/","/sdcard/")

def digest(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()

def read_safe(path:Path,limit:int)->bytes:
    if path.is_symlink() or not path.is_file() or not (0<path.stat().st_size<=limit):
        raise ValueError("SCM candidate source file missing, linked or oversized")
    raw=path.read_bytes()
    if len(raw)!=path.stat().st_size:
        raise ValueError("SCM candidate file size unstable")
    return raw

def validate(candidate:Path):
    if (not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_dir()
            or any(value in str(candidate) for value in FORBIDDEN)
            or {x.name for x in candidate.iterdir()}!=FILES
            or any(x.is_symlink() or not x.is_file() for x in candidate.iterdir())):
        raise ValueError("Unexpected isolated v9 SCM source artifact directory")
    record=json.loads(read_safe(candidate/"sc-manifest.json",16384))
    expected={
        "schema_version":1,"generation":"wine29-v9-scm-client-source-only",
        "source_commit":SOURCE_REV,"source_build_commit":SOURCE_COMMIT,
        "package_intended":"com.charoitx",
        "file":"sc-arm64.exe","image_name":"sc.exe","pe_machine":"0xAA64",
        "sealed_34_provider_count":34,
        "unbundled_imports":[],
        "source_candidate_only":True,"android_apk_built":False,
        "native_elf_included":False,"wine_executed":False,
        "windows_pe_executed":False,"device_tested":False,
        "prefix_created":False,"scm_verified":False,"launch_ready":False,
    }
    for key,val in expected.items():
        if record.get(key)!=val:
            raise ValueError("SCM source candidate manifest mismatch: "+key)
    exe=read_safe(candidate/"sc-arm64.exe",32*1024*1024)
    if len(exe)!=record.get("size") or digest(exe)!=record.get("sha256"):
        raise ValueError("SCM source candidate manifest hash/size invalid")
    if exe[:2]!=b"MZ" or len(exe)<128:
        raise ValueError("SCM candidate DOS header invalid")
    offset=struct.unpack_from("<I",exe,0x3c)[0]
    if not 64<=offset<len(exe)-24 or exe[offset:offset+4]!=b"PE\0\0" or struct.unpack_from("<H",exe,offset+4)[0]!=0xaa64:
        raise ValueError("SCM candidate must be Windows ARM64 executable")
    header=read_safe(candidate/"sc-pe-header.txt",65536).decode("utf-8")
    imports=read_safe(candidate/"sc-coff-imports.txt",65536).decode("utf-8")
    if "ARM64" not in header:
        raise ValueError("Independent LLVM SCM header check failed")
    classifier_path=Path(__file__).resolve().parent/"wine29-imports/classify.py"
    spec=importlib.util.spec_from_file_location("wine29_v9_imports",classifier_path)
    cls=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls)
    ordinary,delay=cls.pe_imports(exe)
    if (ordinary!=record.get("ordinary_imports") or delay!=record.get("delay_imports")
            or "advapi32.dll" not in ordinary or record["unbundled_imports"]
            or not all(name in imports for name in ordinary)):
        raise ValueError("SCM imported dependency graph differs from pinned source")
    return exe,record

def stage(candidate_arg:str,prepared_arg:str):
    candidate=Path(candidate_arg)
    prepared=Path(prepared_arg)
    for path in (candidate,prepared):
        if not path.is_absolute() or path.is_symlink() or any(bad in str(path) for bad in FORBIDDEN):
            raise ValueError("Only isolated CI source and build paths allowed")
    exe,source=validate(candidate)
    assets=prepared/"app/src/main/assets"
    old=[
        assets/"charoite-next/wine29-sealed012/wine29-sealed012-index.json",
        assets/"charoite-next/wine29-v6/wine29-v6-native-index.json",
        assets/"charoite-next/wine29-v7-services/services-index.json",
        assets/"charoite-next/wine29-v8-userenv/userenv-index.json",
    ]
    if not all(f.is_file() and not f.is_symlink() for f in old):
        raise ValueError("Source-coherent v6-v8 candidate assets not present")
    sealed,native,services,userenv=(json.loads(path.read_text()) for path in old)
    if (sealed.get("module_count")!=111
            or any(v.get("wine_source_commit",v.get("native_source_revision"))!=SOURCE_REV
                   for v in (sealed,native,services,userenv))
            or services.get("image_name")!="services.exe"
            or userenv.get("image_name")!="userenv.dll"):
        raise ValueError("v9 source provider ancestry mismatch")
    if any(item.get("path")=="pe/arm64ec/sc.exe" for item in sealed["module_files"]):
        raise ValueError("sc.exe unexpectedly present in historical sealed provider")
    dest=assets/ROOT
    if dest.exists() or dest.is_symlink():
        raise ValueError("Refusing to replace any v9 SCM asset")
    index={
        "schema_version":1,"package":"com.charoitx",
        "wine_source_commit":SOURCE_REV,
        "source_run":SOURCE_RUN,"source_build_commit":SOURCE_COMMIT,
        "source_artifact_id":SOURCE_ARTIFACT,"source_artifact_digest":SOURCE_DIGEST,
        "image_name":"sc.exe","asset":ASSET,"size":len(exe),
        "sha256":digest(exe),"pe_machine":"0xAA64",
        "ordinary_imports":source["ordinary_imports"],
        "delay_imports":source["delay_imports"],
        "unbundled_imports":[],
        "previous_sealed_111_unchanged":True,
        "prior_v6_native_cohort_unchanged":True,
        "prior_v7_services_unchanged":True,
        "prior_v8_userenv_unchanged":True,
        "apk_stage_only":True,
        "windows_executed":False,"prefix_initialized":False,
        "device_tested":False,"scm_verified":False,"launch_ready":False,
    }
    dest.mkdir(parents=True,exist_ok=False)
    (assets/ASSET).write_bytes(exe)
    (assets/INDEX).write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    if digest((assets/ASSET).read_bytes())!=source["sha256"]:
        raise ValueError("Packaged v9 sc.exe SHA-256 mismatch")
    print("WINE29_V9_SC_SOURCE_PINNED_ASSET_SHA256=PASS")
    print("WINE29_V9_OLD_V6_V7_V8_AND_111_COHORTS_UNCHANGED=PASS")
    print("WINE29_V9_PHONE_SERVICE_QUERY_NOT_ATTEMPTED")

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: stage_wine29_v9_sc.py ABS_CANDIDATE_DIR ABS_PREPARED_NEXT")
    stage(sys.argv[1],sys.argv[2])
