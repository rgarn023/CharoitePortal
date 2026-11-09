#!/usr/bin/env python3
"""Stage NEW source-pinned V23 Wine29 prefix-setup assets in experimental Next APK only.
Does not execute PE/Wine, mutate earlier generations, or touch Android private data.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys

REV="c74acb09d51b447f5d5ac56c87608d3ec565a767"
RUN=42552476223
COMMIT="b6d180240adf2e8c354e9a5a016c828ca04a9911"
ARTIFACT=13645473200
DIGEST="sha256:6d86ac6848e81af2190074c0e93f2ecf4aa6fc41cb7a72d15a55dc79d55b8581"
ROOT="charoite-next/wine29-v23-setup"
FILENAMES={"prefix-setup-manifest.json","rundll32-arm64.exe","rpcss-arm64.exe",
           "wine.inf","rundll32-pe-header.txt","rpcss-pe-header.txt",
           "rundll32-coff-imports.txt","rpcss-coff-imports.txt"}
HASHES={"rundll32":"8dce8c98e0c6e443987ae810efbc3e15c23e9947583c5a00e713cf58124316ee",
        "rpcss":"5af9d9557d6a12cb9a91c2fb3cb2cd33119e9c3c30bad66c7b1b122ef30694ff",
        "wine_inf":"5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a"}
FORBIDDEN=("/data/user/","/data/data/","/storage/emulated/","/sdcard/")

def sha(raw): return hashlib.sha256(raw).hexdigest()

def safe_file(p,limit):
    if p.is_symlink() or not p.is_file() or not (0<p.stat().st_size<=limit):
        raise ValueError("Missing/unsafe V23 source file")
    data=p.read_bytes()
    if len(data)!=p.stat().st_size: raise ValueError("Unstable V23 source file")
    return data

def checked_dir(path):
    if not path.is_absolute() or path.is_symlink() or not path.is_dir() or any(s in str(path) for s in FORBIDDEN):
        raise ValueError("V23 accepts only a private ephemeral CI directory")

def validate(source):
    checked_dir(source)
    if {p.name for p in source.iterdir()}!=FILENAMES:
        raise ValueError("V23 source artifact file set changed")
    index=json.loads(safe_file(source/"prefix-setup-manifest.json",16384))
    expected={"schema_version":1,"generation":"wine29-v23-prefix-setup-source-only",
              "source_commit":REV,"source_build_commit":COMMIT,
              "package_intended":"com.charoitx","sealed_34_provider_count":34,
              "source_candidate_only":True,"android_apk_built":False,"wine_executed":False,
              "windows_pe_executed":False,"device_tested":False,"prefix_created":False,
              "scm_verified":False,"launch_ready":False}
    for key,value in expected.items():
        if index.get(key)!=value: raise ValueError("V23 provenance mismatch: "+key)
    if set(index.get("pe",{}))!={"rundll32","rpcss"}: raise ValueError("V23 PE inventory mismatch")
    data={}
    for name,require in (("rundll32","kernelbase.dll"),("rpcss","rpcrt4.dll")):
        entry=index["pe"][name]
        if entry.get("file")!=name+"-arm64.exe" or entry.get("image_name")!=name+".exe" or entry.get("pe_machine")!="0xAA64":
            raise ValueError("V23 candidate identity mismatch")
        raw=safe_file(source/entry["file"],32*1024*1024)
        if len(raw)!=entry.get("size") or sha(raw)!=entry.get("sha256") or sha(raw)!=HASHES[name]:
            raise ValueError("V23 pinned candidate PE hash mismatch")
        if len(raw)<128 or raw[:2]!=b"MZ": raise ValueError("V23 missing DOS header")
        ofs=struct.unpack_from("<I",raw,0x3c)[0]
        if not (64<=ofs<len(raw)-24 and raw[ofs:ofs+4]==b"PE\x00\x00" and struct.unpack_from("<H",raw,ofs+4)[0]==0xaa64):
            raise ValueError("V23 source candidate not Windows ARM64")
        if require not in entry.get("ordinary_imports",[]) or entry.get("delay_imports")!=[] or entry.get("unbundled_imports")!=[]:
            raise ValueError("V23 source PE import gate failed")
        if "ARM64" not in safe_file(source/(name+"-pe-header.txt"),65536).decode("utf-8"):
            raise ValueError("V23 independent PE header report missing")
        data[name]=raw
    entry=index.get("inf",{})
    if entry.get("file")!="wine.inf" or entry.get("arm64_default_service_section") is not True or entry.get("rpcss_install_declared") is not True:
        raise ValueError("V23 Wine installation manifest mismatch")
    raw=safe_file(source/"wine.inf",1024*1024)
    if len(raw)!=entry.get("size") or sha(raw)!=entry.get("sha256") or sha(raw)!=HASHES["wine_inf"]:
        raise ValueError("V23 source-pinned wine.inf mismatch")
    text=raw.decode("utf-8-sig",errors="strict")
    if "[DefaultInstall.ntarm64.Services]" not in text or "AddService=RpcSs" not in text or "[RpcSsService]" not in text:
        raise ValueError("V23 wine.inf missing source-built ARM64 RpcSs installation")
    data["wine_inf"]=raw
    return data,index

def stage(source_arg,prepared_arg):
    source=Path(source_arg); prepared=Path(prepared_arg)
    checked_dir(source); checked_dir(prepared)
    data,manifest=validate(source)
    assets=prepared/"app/src/main/assets"
    predecessors=("wine29-sealed012/wine29-sealed012-index.json",
                  "wine29-v6/wine29-v6-native-index.json",
                  "wine29-v7-services/services-index.json",
                  "wine29-v8-userenv/userenv-index.json",
                  "wine29-v9-sc/sc-index.json")
    prior=[]
    for path in predecessors:
        p=assets/("charoite-next/"+path)
        prior.append(json.loads(safe_file(p,65536)))
    sealed,native,services,userenv,sc=prior
    if sealed.get("module_count")!=111 or sc.get("image_name")!="sc.exe" or services.get("image_name")!="services.exe" or userenv.get("image_name")!="userenv.dll":
        raise ValueError("V23 existing source module ancestry mismatch")
    if any(p.get("wine_source_commit",p.get("native_source_revision"))!=REV for p in prior):
        raise ValueError("V23 source ancestry mismatched")
    dest=assets/ROOT
    if dest.exists() or dest.is_symlink(): raise ValueError("V23 cannot overwrite an existing asset")
    dest.mkdir(parents=True,exist_ok=False)
    records={}
    for name,raw in data.items():
        filename={"rundll32":"rundll32-arm64.exe.bin","rpcss":"rpcss-arm64.exe.bin","wine_inf":"wine.inf"}[name]
        path=dest/filename
        path.write_bytes(raw)
        if sha(path.read_bytes())!=HASHES[name]: raise ValueError("V23 staged asset differs from trusted source")
        records[name]={"asset":ROOT+"/"+filename,"size":len(raw),"sha256":HASHES[name]}
        if name!="wine_inf":
            records[name]["pe_machine"]="0xAA64"
            records[name]["ordinary_imports"]=manifest["pe"][name]["ordinary_imports"]
            records[name]["delay_imports"]=[]
            records[name]["unbundled_imports"]=[]
    index={"schema_version":1,"package":"com.charoitx",
           "wine_source_commit":REV,"source_run":RUN,"source_build_commit":COMMIT,
           "source_artifact_id":ARTIFACT,"source_artifact_digest":DIGEST,
           "assets":records,
           "prior_sealed_111_unchanged":True,"prior_v6_native_unchanged":True,
           "prior_v7_services_unchanged":True,"prior_v8_userenv_unchanged":True,
           "prior_v9_sc_unchanged":True,"apk_stage_only":True,
           "wine_executed":False,"prefix_initialized":False,
           "device_tested":False,"scm_verified":False,"launch_ready":False}
    (dest/"setup-index.json").write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    print("WINE29_V23_SOURCE_PINNED_PREFIX_SETUP_ASSETS=PASS")
    print("WINE29_V23_PRIOR_PRESERVED_MODULES_UNCHANGED=PASS")
    print("WINE29_V23_PHONE_SETUP_AND_SCM_NOT_ATTEMPTED")

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: stage_wine29_v23_setup.py ABS_SOURCE_CANDIDATE ABS_PREPARED_NEXT")
    stage(sys.argv[1],sys.argv[2])
