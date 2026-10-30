#!/usr/bin/env python3
"""APK-package exactly the three source-matched Wine27 Android ELF components.

No extraction to Android writable/executable app data, no Wine session.
Preserves all original Wine22 APK-native ELF and data paths untouched.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

SOURCE_RUN=41130899651
SOURCE_ARTIFACT=13012239618
SOURCE_COMMIT="c74acb09d51b447f5d5ac56c87608d3ec565a767"
ARCHIVE_VERSION="wine10-arm64ec-bootstrap.0.5"
ASSET="charoite-next/wine27-native-probe.json"
ARCHIVE_ASSET="charoite-next/wine-bootstrap-27.bundle"
INDEX_ASSET="charoite-next/wine-bootstrap-27-index.json"
LIBS={
    "wine":("runtime/bin/wine","libcharoite_wine27_loader.so"),
    "wineserver":("runtime/bin/wineserver","libcharoite_wine27_wineserver.so"),
    "ntdll_unix":("runtime/lib/ntdll.so","libcharoite_wine27_ntdll.so"),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def vbundle():
    path=Path(__file__).resolve().parent/"charoite-wine/verify-bootstrap-bundle.py"
    spec=importlib.util.spec_from_file_location("verified_wine27_native_archive",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate_evidence(manifest,index,raw):
    if (manifest.get("version")!=ARCHIVE_VERSION
            or manifest.get("source_commit")!=SOURCE_COMMIT
            or manifest.get("android_package")!="com.charoitx"
            or manifest.get("component_count")!=26
            or manifest.get("nls_count")!=76
            or any(manifest.get(k) is not False for k in (
                "launch_ready","installable","prefix_created",
                "device_tested","anti_cheat_supported"))
            or index.get("source_run")!=SOURCE_RUN
            or index.get("source_artifact")!=SOURCE_ARTIFACT
            or index.get("wine_source_sha")!=SOURCE_COMMIT
            or index.get("archive_sha256")!=sha(raw)
            or index.get("bundle_version")!=ARCHIVE_VERSION
            or index.get("native_elf_in_archive")!=3):
        raise ValueError("Wine27 native source lineage or APK archive identity failed")
    files={}
    for key,(source,name) in LIBS.items():
        e=manifest["components"].get(key)
        if (not isinstance(e,dict) or e.get("path")!=source or e.get("format")!="ELF"
                or e.get("machine")!="AArch64"
                or not isinstance(e.get("needed"),list)
                or "libwine.so" in e["needed"]
                or not isinstance(e.get("load_alignments"),list)
                or any(x<16384 for x in e["load_alignments"])):
            raise ValueError("Unverified Wine27 native ELF and dependencies")
        files[key]={"library_filename":name,"source_path":source,
                    "sha256":e["sha256"],"size":e["size"],
                    "native_needed":e["needed"]}
    return {
        "schema_version":1,"package":"com.charoitx",
        "source_run":SOURCE_RUN,"source_artifact":SOURCE_ARTIFACT,
        "wine_source_commit":SOURCE_COMMIT,
        "archive_version":ARCHIVE_VERSION,
        "archive_sha256":sha(raw),
        "version_arg":"--version",
        "native_components":files,
        "stage_version":"wine10-arm64ec-bootstrap-0.6-staged",
        "purpose":"Source-verified APK-owned Wine27 native --version probes only",
        "launch_ready":False,"wineboot_tested":False,
        "prefix_created":False,"windows_exe_executed":False,
        "fex_installed":False,"graphics_verified":False,
        "anti_cheat_supported":False
    }

def stage(archive,upstream):
    if Path(archive).is_symlink() or Path(upstream).is_symlink():
        raise ValueError("Symlink Wine27 source input")
    archive=Path(archive).resolve()
    app=Path(upstream).resolve()/"app/src/main"
    if not (app/"AndroidManifest.xml").is_file() or any(
            x in str(app) for x in ("/data/data/","/data/user/","/storage/emulated/")):
        raise ValueError("Not isolated Next build tree")
    if not archive.is_file() or archive.stat().st_size>128*1024*1024:
        raise ValueError("Missing or oversized Wine27 source artifact")
    ver=vbundle()
    manifest,review=ver.verify(archive)
    raw=archive.read_bytes()
    index_path=app/"assets"/INDEX_ASSET
    bundle_path=app/"assets"/ARCHIVE_ASSET
    if not index_path.is_file() or not bundle_path.is_file():
        raise ValueError("Full Wine27 archive and PE staging not packaged")
    if sha(bundle_path.read_bytes())!=sha(raw):
        raise ValueError("Wine27 native cohort differs from packaged PE/NLS data")
    index=json.loads(index_path.read_text(encoding="utf-8"))
    evidence=validate_evidence(manifest,index,raw)
    output=app/"assets"/ASSET
    if output.exists(): raise ValueError("Refusing to replace Wine27 ELF evidence")
    dests=[]
    for key,entry in evidence["native_components"].items():
        dst=app/"jniLibs/arm64-v8a"/entry["library_filename"]
        if dst.exists(): raise ValueError("Refusing to replace pre-existing native Wine27 ELF")
        dests.append((key,entry,dst))
    with tarfile.open(archive,"r:gz") as tar:
        for key,entry,dst in dests:
            member=tar.getmember(entry["source_path"])
            if not member.isfile() or member.size!=entry["size"]:
                raise ValueError("Native ELF source member changed")
            data=tar.extractfile(member).read()
            if len(data)!=entry["size"] or sha(data)!=entry["sha256"]:
                raise ValueError("Wine27 native binary SHA-256 mismatch")
            # Original source-built loader includes Android lib-directory ntdll lookup.
            if key=="wine" and b"CHAROITE_WINE27_NATIVE_DIR" not in data:
                raise ValueError("Wine27 loader lacks isolated native cohort override")
            if key in ("ntdll_unix","wineserver") and b"CHAROITE_WINE26_DATA_DIR" not in data:
                raise ValueError("Wine27 native NLS override absent: "+key)
            if key=="wine" and b"libcharoite_wine27_ntdll.so" not in data:
                raise ValueError("Wine27 native ntdll explicit identity absent")
            from importlib.util import spec_from_file_location, module_from_spec
            spec=spec_from_file_location("old_native_elf_shape",Path(__file__).resolve().parent/"stage_native_wine_loader.py")
            native=module_from_spec(spec);spec.loader.exec_module(native)
            native.validate_loader(data)
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(data)
            dst.chmod(0o755)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    gradle=Path(upstream).resolve()/"app/build.gradle"
    cfg=gradle.read_text(encoding="utf-8")
    if any(entry["library_filename"] in cfg for entry in evidence["native_components"].values()):
        raise ValueError("Duplicate Wine27 doNotStrip rules")
    cfg+="\nandroid {\n    packagingOptions {\n"
    for entry in evidence["native_components"].values():
        cfg+='        doNotStrip "**/'+entry["library_filename"]+'"\n'
    cfg+="    }\n}\n"
    gradle.write_text(cfg,encoding="utf-8")
    print("CHAROITE_NEXT_WINE27_NATIVE_SOURCE_COHORT_VERIFIED=PASS")
    print("CHAROITE_NEXT_WINE27_THREE_NATIVE_ELF_APK_PACKAGE=PASS")
    print("WINEBOOT_NOT_TESTED=true")
    return evidence

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: stage_wine27_native.py SOURCE_26_ARCHIVE NEXT_BUILD_TREE")
    stage(sys.argv[1],sys.argv[2])
