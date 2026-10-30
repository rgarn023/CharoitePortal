#!/usr/bin/env python3
"""Stage one FULL coherent 26-component Wine archive as inert Next-only APK data.

Never combine rebuilt PE modules with the APK's original native Wine loader:
the 26-component archive remains a separate generation with its own versioned
PE/NLS data slot. All 3 new native ELFs remain inert inside the audited archive.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

RUN=41130899651
ARTIFACT=13012239618
SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
VERSION="wine10-arm64ec-bootstrap.0.5"
ASSET="charoite-next/wine-bootstrap-27.bundle"
INDEX="charoite-next/wine-bootstrap-27-index.json"
ROOT="charoite-next/wine27-modules"
MAX_ARCHIVE=128*1024*1024
MAX_MODULE=32*1024*1024
MAX_TOTAL=128*1024*1024
MAX_INDEX=65536

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verifier():
    file=Path(__file__).resolve().parent/"charoite-wine/verify-bootstrap-bundle.py"
    spec=importlib.util.spec_from_file_location("charoite_wine27_verified_bundle",file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def make_index(manifest,review,raw,old_manifest):
    if (manifest.get("version")!=VERSION
            or manifest.get("source_commit")!=SOURCE
            or manifest.get("android_package")!="com.charoitx"
            or manifest.get("component_count")!=26
            or manifest.get("nls_count")!=76
            or any(manifest.get(x) is not False for x in (
                "launch_ready","installable","prefix_created",
                "device_tested","anti_cheat_supported"))
            or old_manifest.get("version")!="wine10-arm64ec-bootstrap.0.4"
            or old_manifest.get("source_commit")!=SOURCE
            or old_manifest.get("source_files")!=manifest.get("source_files")
            or not 0<len(raw)<=MAX_ARCHIVE):
        raise ValueError("New Wine archive or original source provenance is untrusted")
    comps=manifest.get("components")
    nls=manifest.get("nls_files")
    if not isinstance(comps,dict) or not isinstance(nls,dict):
        raise ValueError("Missing source-verified module inventory")
    extras={"bcrypt","msvcrt","sechost","secur32"}
    if not extras.issubset(comps):
        raise ValueError("Audited new security DLLs missing")
    records=[]
    for name,record in comps.items():
        if record.get("format")!="PE":
            if record.get("format")!="ELF":
                raise ValueError("Unexpected Wine component format")
            continue
        records.append(record)
    records.extend(nls.values())
    if len(records)!=99 or len(nls)!=76:
        raise ValueError("Expected exactly 23 PE plus 76 NLS modules")
    files=[]
    total=0
    for rec in records:
        source=rec.get("path")
        if not isinstance(source,str):
            raise ValueError("Missing source path")
        if source.startswith("runtime/pe/arm64ec/") and source.endswith(".dll"):
            local=source[len("runtime/"):]
        elif source=="runtime/pe/arm64/wineboot.exe":
            local="pe/arm64/wineboot.exe"
        elif source.startswith("runtime/nls/") and source.endswith(".nls"):
            local=source[len("runtime/"):]
        else:
            raise ValueError("Unapproved Wine27 module path")
        if ".." in local or not all(c.isalnum() or c in "/._-" for c in local):
            raise ValueError("Unsafe staged path")
        size=rec.get("size")
        digest=rec.get("sha256")
        if (not isinstance(size,int) or size<=0 or size>MAX_MODULE
                or not isinstance(digest,str) or len(digest)!=64
                or any(x not in "0123456789abcdef" for x in digest)):
            raise ValueError("Invalid source module SHA or size")
        total+=size
        files.append({"path":local,"source":source,"size":size,"sha256":digest,
                      "asset":ROOT+"/"+local.replace("/","_")+".bin"})
    files.sort(key=lambda x:x["path"])
    if (total>MAX_TOTAL or len(set(x["path"] for x in files))!=99
            or len(set(x["asset"] for x in files))!=99):
        raise ValueError("Duplicate or excessive Wine27 file inventory")
    gaps=review.get("windows_imports_not_bundled")
    if (not isinstance(gaps,list) or gaps!=sorted(set(gaps))
            or manifest.get("window_imports_unresolved_count")!=len(gaps)
            or len(gaps)!=20):
        raise ValueError("Measured Wine27 import gaps changed; review them first")
    return {
        "schema_version":1,"android_package":"com.charoitx",
        "wine_source_sha":SOURCE,"source_run":RUN,"source_artifact":ARTIFACT,
        "bundle_version":VERSION,"archive_asset":ASSET,
        "archive_sha256":sha(raw),"archive_size":len(raw),
        "component_count":26,"pe_count":23,"native_elf_in_archive":3,
        "nls_count":76,"module_count":99,"modules_total_bytes":total,
        "module_files":files,"remaining_observed_pe_imports":gaps,
        "remaining_observed_pe_imports_count":len(gaps),
        "cohort":"Full 26-component source-build is separate from existing v0.38 native loader and staged Wine22",
        "launch_ready":False,"installable_as_runtime":False,
        "native_elf_installed":False,"prefix_created":False,
        "wineboot_tested":False,"fex_installed":False,
        "graphics_verified":False,"anti_cheat_supported":False
    }

def stage(archive,upstream):
    if Path(archive).is_symlink() or Path(upstream).is_symlink():
        raise ValueError("Symlink input forbidden")
    archive=Path(archive).resolve()
    app=Path(upstream).resolve()/"app/src/main"
    if not (app/"AndroidManifest.xml").is_file() or any(
            x in str(app) for x in ("/data/data/","/data/user/","/storage/emulated/")):
        raise ValueError("Not a fresh separate Next CI build tree")
    if not archive.is_file() or not 0<archive.stat().st_size<=MAX_ARCHIVE:
        raise ValueError("Oversize or missing source-built Wine27 archive")
    ver=verifier()
    manifest,review=ver.verify(archive)
    old_archive=app/"assets/charoite-next/wine-bootstrap-22.bundle"
    old_index=app/"assets/charoite-next/wine-bootstrap-payload.json"
    if not old_archive.is_file() or not old_index.is_file():
        raise ValueError("Missing original user-tested Wine22 APK source baseline")
    old_bytes=old_archive.read_bytes()
    index_old=json.loads(old_index.read_text(encoding="utf-8"))
    if sha(old_bytes)!=index_old.get("archive_sha256"):
        raise ValueError("Original pinned source archive hash mismatch")
    # Read-only audit of original FULL Wine22 bundle; both generations
    # retain the exact patched source files but do not mix binary cohorts.
    old_manifest,unused=ver.verify(old_archive)
    raw=archive.read_bytes()
    # Independently prove this archive comes from the Android-only 0800
    # native NLS/cohort source fix, not an old 0.5 build with the same
    # upstream Wine version and the same PE module inventory.
    with tarfile.open(archive,"r:gz") as evidence_tar:
        delta=evidence_tar.extractfile("source/charoite-source-delta.patch").read()
    for marker in (b"CHAROITE_WINE26_DATA_DIR", b"CHAROITE_WINE27_NATIVE_DIR",
                   b"libcharoite_wine27_ntdll.so"):
        if marker not in delta:
            raise ValueError("New native NLS/source-cohort patch not present in archive")
    index=make_index(manifest,review,raw,old_manifest)
    payload=app/"assets"/ASSET
    target_index=app/"assets"/INDEX
    module_root=app/"assets"/ROOT
    if payload.exists() or target_index.exists() or module_root.exists():
        raise ValueError("Refusing to overwrite an existing Wine generation")
    module_root.mkdir(parents=True,exist_ok=False)
    payload.write_bytes(raw)
    if sha(payload.read_bytes())!=index["archive_sha256"]:
        raise ValueError("Packaged Wine27 source hash failed")
    with tarfile.open(archive,"r:gz") as tar:
        for item in index["module_files"]:
            member=tar.getmember(item["source"])
            if not member.isfile() or member.size!=item["size"]:
                raise ValueError("Wrong verified PE/NLS source member type")
            data=tar.extractfile(member).read()
            if sha(data)!=item["sha256"]:
                raise ValueError("Wine27 module source hash changed")
            (app/"assets"/item["asset"]).write_bytes(data)
    encoded=(json.dumps(index,indent=2,sort_keys=True)+"\n").encode("utf-8")
    if len(encoded)>MAX_INDEX:
        raise ValueError("Oversized Wine27 module index")
    target_index.write_bytes(encoded)
    print("CHAROITE_NEXT_WINE27_FULL_SOURCE_ARCHIVE=PASS")
    print("CHAROITE_NEXT_WINE27_99_PE_NLS_DATA_FILES=PASS")
    print("CHAROITE_NEXT_WINE27_OBSERVED_IMPORT_GAPS="+str(len(index["remaining_observed_pe_imports"])))
    print("CHAROITE_NEXT_WINE27_LAUNCH_READY=false")
    return index

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("Usage: stage_wine27.py SOURCE_VERIFIED_26_ARCHIVE NEXT_UPSTREAM")
    stage(sys.argv[1],sys.argv[2])
