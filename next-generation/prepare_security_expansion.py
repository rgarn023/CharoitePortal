#!/usr/bin/env python3
"""Fail-closed CI-only bridge for a newly verified Wine PE dependency extension.

The Android APK still uses its independently attested 22-component source.
An extended 26-component archive is accepted only if EVERY old component,
Wine NLS table and pinned source blob is byte-for-byte identical, with exactly
four audited ARM64EC DLL additions. The new files remain inert APK data assets.
No native ELF is extracted, no runtime can launch, and no phone storage touched.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tarfile

SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
BASE_VERSION="wine10-arm64ec-bootstrap.0.4"
NEW_VERSION="wine10-arm64ec-bootstrap.0.5"
NAMES=("bcrypt","msvcrt","sechost","secur32")
NEW_ASSET_ROOT="charoite-next/wine-security-additions"
NEW_INDEX="charoite-next/wine-security-expansion.json"
MAX_ARCHIVE=128*1024*1024
MAX_DLL=32*1024*1024
MAX_TOTAL=64*1024*1024

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def verifier():
    path=Path(__file__).resolve().parent/"charoite-wine/verify-bootstrap-bundle.py"
    spec=importlib.util.spec_from_file_location("charoite_security_full_bundle_verifier",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def make_index(old,new,review,old_raw,new_raw,run,artifact):
    if (old.get("version")!=BASE_VERSION or new.get("version")!=NEW_VERSION
            or old.get("source_commit")!=SOURCE or new.get("source_commit")!=SOURCE
            or old.get("android_package")!="com.charoitx" or new.get("android_package")!="com.charoitx"
            or old.get("component_count")!=22 or new.get("component_count")!=26
            or old.get("nls_count")!=76 or new.get("nls_count")!=76
            or any(old.get(flag) is not False or new.get(flag) is not False for flag in (
                "launch_ready","installable","prefix_created","device_tested","anti_cheat_supported"))
            or not isinstance(run,int) or run<=0 or not isinstance(artifact,int) or artifact<=0
            or not 0<len(old_raw)<=MAX_ARCHIVE or not 0<len(new_raw)<=MAX_ARCHIVE):
        raise ValueError("Unsafe or unverified next-generation source expansion")
    old_components=old.get("components")
    new_components=new.get("components")
    if not isinstance(old_components,dict) or not isinstance(new_components,dict):
        raise ValueError("Missing source-built component inventory")
    if (set(new_components)-set(old_components)!=set(NAMES)
            or set(old_components)-set(new_components)):
        raise ValueError("Unapproved security module set")
    for name,entry in old_components.items():
        if entry!=new_components.get(name):
            raise ValueError("Existing Wine component changed: "+name)
    for label in ("nls_files","source_files","startup_dependency_manifest_sha256",
                  "com_dependency_manifest_sha256"):
        if old.get(label)!=new.get(label):
            raise ValueError("Existing pinned Wine source/NLS provenance changed: "+label)
    if (not isinstance(new.get("services_dependency_manifest_sha256"),str)
            or len(new["services_dependency_manifest_sha256"])!=64):
        raise ValueError("Unverified services source manifest")
    gap=review.get("windows_imports_not_bundled")
    if not isinstance(gap,list) or gap!=sorted(set(gap)) or any(
            not isinstance(x,str) or not x.endswith(".dll") for x in gap):
        raise ValueError("Untrusted new Windows import gap inventory")
    if new.get("window_imports_unresolved_count")!=len(gap):
        raise ValueError("Dependency inventory count inconsistent")
    additions=[]
    size_total=0
    for name in NAMES:
        e=new_components[name]
        src=f"runtime/pe/arm64ec/{name}.dll"
        size=e.get("size")
        hash_value=e.get("sha256")
        if (e.get("path")!=src or e.get("format")!="PE"
                or e.get("machine")!="0xA641"
                or not isinstance(size,int) or not 0<size<=MAX_DLL
                or not isinstance(hash_value,str) or len(hash_value)!=64 or
                any(x not in "0123456789abcdef" for x in hash_value)):
            raise ValueError("Unsafe or non-ARM64EC added DLL")
        size_total+=size
        additions.append({"name":name,"source":src,"size":size,
                          "sha256":hash_value,
                          "asset":f"{NEW_ASSET_ROOT}/{name}.bin"})
    if size_total>MAX_TOTAL:
        raise ValueError("Security module data exceeds size bound")
    return {"schema_version":1,"android_package":"com.charoitx",
            "wine_source_sha":SOURCE,"source_run":run,"source_artifact":artifact,
            "base_version":BASE_VERSION,"extension_version":NEW_VERSION,
            "base_archive_sha256":digest(old_raw),"extended_archive_sha256":digest(new_raw),
            "base_components":22,"extended_components":26,"nls_count":76,
            "added_pe_count":4,"added_size":size_total,"added_files":additions,
            "remaining_observed_pe_imports":gap,
            "remaining_observed_pe_imports_count":len(gap),
            "status":"CI-verified, inert APK assets only; NOT an installed Wine runtime",
            "launch_ready":False,"prefix_created":False,"wineboot_tested":False,
            "native_elf_added":False,"fex_installed":False,"graphics_verified":False,
            "anti_cheat_supported":False}

def stage(old_archive,new_archive,upstream,run,artifact):
    old_archive=Path(old_archive).resolve()
    new_archive=Path(new_archive).resolve()
    upstream=Path(upstream).resolve()
    main=upstream/"app/src/main"
    if not (main/"AndroidManifest.xml").is_file() or any(
        token in str(main) for token in ("/data/data/","/data/user/","/storage/emulated/")
    ):
        raise ValueError("Not an isolated Charoite Next CI build tree")
    for path in (old_archive,new_archive):
        if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<=MAX_ARCHIVE:
            raise ValueError("Unsafe archive source")
    v=verifier()
    old,unused=v.verify(old_archive)
    new,review=v.verify(new_archive)
    old_raw,new_raw=old_archive.read_bytes(),new_archive.read_bytes()
    index=make_index(old,new,review,old_raw,new_raw,run,artifact)
    # Assert APK's already-staged immutable 22 archive is identical. It cannot
    # silently switch its loader, native ntdll, PE baseline or Japanese tables.
    existing=main/"assets/charoite-next/wine-bootstrap-22.bundle"
    if not existing.is_file() or digest(existing.read_bytes())!=index["base_archive_sha256"]:
        raise ValueError("APK pinned 22-component archive does not match source")
    index_dest=main/"assets"/NEW_INDEX
    root=main/"assets"/NEW_ASSET_ROOT
    if index_dest.exists() or root.exists():
        raise ValueError("Refusing to overwrite Wine extension assets")
    root.mkdir(parents=True,exist_ok=False)
    with tarfile.open(new_archive,"r:gz") as tar:
        for entry in index["added_files"]:
            member=tar.getmember(entry["source"])
            if not member.isfile() or member.size!=entry["size"]:
                raise ValueError("Wrong extended source module type or size")
            content=tar.extractfile(member).read()
            if digest(content)!=entry["sha256"]:
                raise ValueError("Extended PE module hash mismatch")
            (main/"assets"/entry["asset"]).write_bytes(content)
    index_dest.write_text(json.dumps(index,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("CHAROITE_NEXT_SECURITY_ADDON_SOURCE_MATCH_VERIFIED=PASS")
    print("CHAROITE_NEXT_SECURITY_ADDON_FOUR_PE_SHA256_VERIFIED=PASS")
    print("CHAROITE_NEXT_REMAINING_OBSERVED_PE_IMPORT_GAPS="+str(len(index["remaining_observed_pe_imports"])))
    print("CHAROITE_NEXT_MODERN_LAUNCH_READY=false")
    return index

if __name__=="__main__":
    if len(sys.argv)!=6:
        raise SystemExit("Usage: prepare_security_expansion.py VERIFIED_22_ARCHIVE VERIFIED_26_ARCHIVE NEXT_UPSTREAM RUN_ID ARTIFACT_ID")
    stage(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]))
