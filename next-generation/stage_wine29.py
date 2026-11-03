#!/usr/bin/env python3
"""Inert, isolated Charoite Next Wine29 PE/NLS staging from verified source 27.
Never loads Wine/ELF, runs wineboot, opens a user prefix, or changes older slots.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import tarfile

SOURCE_RUN=41586391767
SOURCE_ARTIFACT=13208541305
SOURCE_SHA="c74acb09d51b447f5d5ac56c87608d3ec565a767"
VERSION="wine10-arm64ec-bootstrap.0.6"
ASSET="charoite-next/wine-bootstrap-29.bundle"
INDEX="charoite-next/wine-bootstrap-29-index.json"
ROOT="charoite-next/wine29-modules"
MAX_ARCHIVE=128*1024*1024
MAX_SIZE=32*1024*1024
MAX_TOTAL=128*1024*1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verifier():
    file=Path(__file__).resolve().parent/"charoite-wine/verify-bootstrap-bundle.py"
    spec=importlib.util.spec_from_file_location("charoite_wine29_full_verifier",file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def index_for(manifest,review,archive,prior_manifest,prior_index):
    if (manifest.get("version")!=VERSION or
        manifest.get("android_package")!="com.charoitx" or
        manifest.get("source_commit")!=SOURCE_SHA or
        manifest.get("component_count")!=27 or
        manifest.get("nls_count")!=76 or
        prior_manifest.get("version")!="wine10-arm64ec-bootstrap.0.5" or
        prior_manifest.get("component_count")!=26 or
        prior_index.get("module_count")!=99 or
        not 0<len(archive)<=MAX_ARCHIVE):
        raise ValueError("Source 27 or original Wine28 generation not verified")
    for key in ("launch_ready","installable","prefix_created","device_tested",
                "anti_cheat_supported"):
        if manifest.get(key) is not False:
            raise ValueError("Wine29 must remain non-runnable")
    comps=manifest.get("components")
    nls=manifest.get("nls_files")
    if not isinstance(comps,dict) or not isinstance(nls,dict):
        raise ValueError("Missing Wine29 source records")
    prior_components=set(prior_manifest.get("components",{}))
    if set(comps)!=prior_components|{"apisetschema"}:
        raise ValueError("Wine29 component names not exactly old 26 plus API-set")
    api=comps["apisetschema"]
    if (api.get("path")!="runtime/pe/arm64ec/apisetschema.dll" or
        api.get("format")!="PE" or
        api.get("api_set_namespace_version")!=6 or
        api.get("machine") not in ("0xAA64","0xA641")):
        raise ValueError("Missing data-only Wine10 ARM64 API-set schema v6")
    old_source=prior_manifest["source_files"]
    new_source=manifest["source_files"]
    for name in ("COPYING.LIB","LICENSE","WEHAVEPHONES-MIT.txt","Wine-NLS-Makefile.in"):
        if old_source[name]["sha256"]!=new_source[name]["sha256"]:
            raise ValueError("Pinned licenses or NLS source changed")
    if old_source["charoite-source-delta.patch"]["sha256"]==new_source["charoite-source-delta.patch"]["sha256"]:
        raise ValueError("New loader source delta missing")
    if (not isinstance(review.get("windows_imports_not_bundled"),list) or
        review["windows_imports_not_bundled"]!=prior_index.get("remaining_observed_pe_imports")):
        raise ValueError("New import gaps changed without review")
    records=[]
    for name,rec in comps.items():
        if rec.get("format")=="ELF":
            # These same-built ELFs remain INERT in the source archive. They
            # are NOT installed over any old APK native library generation.
            continue
        if rec.get("format")!="PE": raise ValueError("Unknown component type")
        records.append(rec)
    records.extend(nls.values())
    if len(records)!=100 or len(nls)!=76:
        raise ValueError("Expected 24 PE plus all 76 Wine NLS files")
    out=[]
    total=0
    for rec in records:
        source=rec.get("path")
        if not isinstance(source,str):raise ValueError("Missing source member")
        if source.startswith("runtime/pe/arm64ec/") and source.endswith(".dll"):
            local=source[len("runtime/"):]
        elif source=="runtime/pe/arm64/wineboot.exe":
            local="pe/arm64/wineboot.exe"
        elif source.startswith("runtime/nls/") and source.endswith(".nls"):
            local=source[len("runtime/"):]
        else:
            raise ValueError("Untrusted Wine29 member path")
        if (".." in local or local.startswith("/") or
            not all(x.isalnum() or x in "/._-" for x in local)):
            raise ValueError("Unsafe Wine29 local path")
        size=rec.get("size")
        digest=rec.get("sha256")
        if (not isinstance(size,int) or not 0<size<=MAX_SIZE or
            not isinstance(digest,str) or len(digest)!=64 or
            any(x not in "0123456789abcdef" for x in digest)):
            raise ValueError("Invalid Wine29 source member size or hash")
        total+=size
        out.append({"path":local,"source":source,"size":size,"sha256":digest,
                    "asset":ROOT+"/"+local.replace("/","_")+".bin"})
    out.sort(key=lambda row:row["path"])
    if (total>MAX_TOTAL or len(set(row["path"] for row in out))!=100 or
        len(set(row["asset"] for row in out))!=100):
        raise ValueError("Wine29 duplicated or oversized source assets")
    return {"schema_version":1,"package":"com.charoitx",
        "source_run":SOURCE_RUN,"source_artifact":SOURCE_ARTIFACT,
        "source_sha":SOURCE_SHA,"bundle_version":VERSION,
        "archive_asset":ASSET,"archive_sha256":sha(archive),
        "archive_size":len(archive),"component_count":27,
        "native_elf_in_archive":3,"native_elf_installed":False,
        "pe_count":24,"nls_count":76,"module_count":100,
        "module_files":out,"modules_total_bytes":total,
        "remaining_observed_pe_imports":review["windows_imports_not_bundled"],
        "api_set_name":"apisetschema.dll",
        "api_set_sha256":api["sha256"],
        "api_set_namespace_version":6,
        "status":"inert-source-data-only",
        "launch_ready":False,"installable_as_runtime":False,
        "prefix_created":False,"wineboot_tested":False,
        "fex_installed":False,"graphics_verified":False,
        "anti_cheat_supported":False}

def stage(archive,upstream):
    archive=Path(archive)
    upstream=Path(upstream)
    if archive.is_symlink() or upstream.is_symlink():
        raise ValueError("Symlink inputs forbidden")
    archive=archive.resolve()
    app=upstream.resolve()/"app/src/main"
    if (not (app/"AndroidManifest.xml").is_file() or
        any(fragment in str(app) for fragment in ("/data/data/","/data/user/","/storage/emulated/"))):
        raise ValueError("Not an isolated CI Next source tree")
    if not archive.is_file() or not 0<archive.stat().st_size<=MAX_ARCHIVE:
        raise ValueError("Missing or oversized Wine29 coherent source bundle")
    ver=verifier()
    manifest,review=ver.verify(archive)
    old_archive=app/"assets/charoite-next/wine-bootstrap-28.bundle"
    old_index=app/"assets/charoite-next/wine-bootstrap-28-index.json"
    if not old_archive.is_file() or not old_index.is_file():
        raise ValueError("Missing original Wine28 source-verified APK baseline")
    prior_index=json.loads(old_index.read_text(encoding="utf-8"))
    old=old_archive.read_bytes()
    if sha(old)!=prior_index.get("archive_sha256"):
        raise ValueError("Original Wine28 archive digest drift")
    prior_manifest,_=ver.verify(old_archive)
    raw=archive.read_bytes()
    # Require the separately verified fail-closed API-set loader patch.
    with tarfile.open(archive,"r:gz") as t:
        delta=t.extractfile("source/charoite-source-delta.patch").read()
    for marker in (b"CHAROITE_WINE28_PE_DIR",b"apisetschema.dll",
                   b"verified isolated Wine28 API-set PE is absent or unreadable"):
        if marker not in delta:
            raise ValueError("New source-backed Wine29 API-set lookup unavailable")
    index=index_for(manifest,review,raw,prior_manifest,prior_index)
    assets=app/"assets"
    target=assets/ASSET
    index_path=assets/INDEX
    root=assets/ROOT
    if target.exists() or index_path.exists() or root.exists():
        raise ValueError("Refusing overwrite of any existing Wine29 slot")
    root.mkdir(parents=True,exist_ok=False)
    target.write_bytes(raw)
    if sha(target.read_bytes())!=index["archive_sha256"]:
        raise ValueError("Wine29 source archive changed during packaging")
    with tarfile.open(archive,"r:gz") as t:
        for info in index["module_files"]:
            member=t.getmember(info["source"])
            if not member.isfile() or member.size!=info["size"]:
                raise ValueError("Wrong source archive member")
            data=t.extractfile(member).read()
            if sha(data)!=info["sha256"]:
                raise ValueError("Wine29 source member verification failed")
            (assets/info["asset"]).write_bytes(data)
    encoded=(json.dumps(index,sort_keys=True,indent=2)+"\n").encode()
    if len(encoded)>65536: raise ValueError("Oversized Wine29 module index")
    index_path.write_bytes(encoded)
    print("CHAROITE_NEXT_WINE29_27_COMPONENT_SOURCE_DATA=PASS")
    print("CHAROITE_NEXT_WINE29_100_PE_NLS_ASSETS=PASS")
    print("CHAROITE_NEXT_WINE29_APISET_NAMESPACE_V6=PASS")
    print("CHAROITE_NEXT_WINE29_NATIVE_ELF_INSTALLED=false")
    print("CHAROITE_NEXT_WINE29_LAUNCH_READY=false")
    return index

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("Usage: stage_wine29.py VERIFIED_27_SOURCE_ARCHIVE NEXT_UPSTREAM")
    stage(sys.argv[1],sys.argv[2])
