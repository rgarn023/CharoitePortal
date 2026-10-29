#!/usr/bin/env python3
"""Stage only an audited, same-build Android Wine ELF for safe --version probing.

Downloaded source archive MUST be the specific successful GitHub CI output.
Never unpack arbitrary tar paths or modify installed app/game/prefix files.
The separate ARM64 Wine binary is NOT a complete runtime.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import struct
import sys
import tarfile

SOURCE_RUN = 40898982875
SOURCE_ARTIFACT = 12908731604
SOURCE_SHA = "5d07e29fdba6552033d5f1a1a50ff1cc2fffe420"
WINE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
LIB = "libcharoite_wine_loader.so"
NTDLL_LIB = "libcharoite_wine_ntdll.so"
ASSET = "charoite-next/wine-native-probe.json"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_loader(data):
    if len(data)<64 or data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Not a little-endian ELF64 loader")
    if struct.unpack_from("<H",data,16)[0] != 3:
        raise ValueError("Loader is not ELF ET_DYN/PIE")
    if struct.unpack_from("<H",data,18)[0] != 183:
        raise ValueError("Loader is not Linux/Android AArch64")
    return True

def stage(artifact, upstream):
    artifact=Path(artifact).resolve()
    upstream=Path(upstream).resolve()
    app=upstream/"app/src/main"
    if (not (app/"AndroidManifest.xml").is_file() or
        not (app/"assets/charoite-next/engine-reference.json").is_file()):
        raise ValueError("Missing isolated Next APK build overlay")
    if any(term in str(app) for term in ("/data/data/","/data/user/","/storage/emulated/")):
        raise ValueError("Staging prohibited in installed Android data")
    spec=importlib.util.spec_from_file_location(
        "coherent_wine_verify",
        Path(__file__).resolve().parent/"charoite-wine"/"verify-bootstrap-bundle.py")
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest, report=verifier.verify(artifact)
    if (manifest.get("version")!="wine10-arm64ec-bootstrap.0.4" or
        manifest.get("source_commit")!=WINE_SHA or
        manifest.get("component_count")!=22 or
        manifest.get("nls_count")!=76 or
        manifest.get("android_package")!="com.charoitx" or
        any(manifest.get(key) is not False for key in
            ("launch_ready","installable","prefix_created","device_tested","anti_cheat_supported"))):
        raise ValueError("Unexpected compiled Wine source or dishonest readiness")
    loader=manifest["components"]["wine"]
    if loader.get("path")!="runtime/bin/wine" or loader.get("format")!="ELF":
        raise ValueError("Source component is not Android Wine executable")
    ntdll=manifest["components"]["ntdll_unix"]
    if ntdll.get("path")!="runtime/lib/ntdll.so" or ntdll.get("format")!="ELF":
        raise ValueError("Bundled native Wine ntdll is missing")
    with tarfile.open(artifact,"r:gz") as tar:
        raw=tar.extractfile("runtime/bin/wine").read()
        ntdll_raw=tar.extractfile("runtime/lib/ntdll.so").read()
    validate_loader(ntdll_raw)
    if ntdll.get("size")!=len(ntdll_raw) or ntdll.get("sha256")!=digest(ntdll_raw):
        raise ValueError("Native ntdll differs from independently audited build")
    if b"CHAROITE_NTDLL_NATIVE_DIR" not in raw:
        raise ValueError("APK Wine loader lacks source-patched Android ntdll fallback")
    validate_loader(raw)
    if loader.get("size")!=len(raw) or loader.get("sha256")!=digest(raw):
        raise ValueError("Wine loader differs from independently audited build")
    if not isinstance(loader.get("needed"),list):
        raise ValueError("Missing loader DT_NEEDED inventory")
    if "libwine.so" in loader["needed"]:
        raise ValueError("Additional native Wine library required before isolated probe")
    dest=app/"jniLibs/arm64-v8a"/LIB
    ntdll_dest=app/"jniLibs/arm64-v8a"/NTDLL_LIB
    info=app/"assets"/ASSET
    if dest.exists() or ntdll_dest.exists() or info.exists():
        raise ValueError("Refusing to overwrite existing native smoke payload")
    dest.parent.mkdir(parents=True,exist_ok=True)
    info.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(raw)
    dest.chmod(0o755)
    ntdll_dest.write_bytes(ntdll_raw)
    ntdll_dest.chmod(0o755)
    evidence={
        "schema_version":1,
        "purpose":"User-initiated source-built Android Wine ELF --version probe only",
        "source_run":SOURCE_RUN,
        "source_artifact":SOURCE_ARTIFACT,
        "source_code_sha":SOURCE_SHA,
        "wine_source_sha":WINE_SHA,
        "android_package":"com.charoitx",
        "native_library_filename":LIB,
        "ntdll_native_library_filename":NTDLL_LIB,
        "ntdll_sha256":digest(ntdll_raw),
        "ntdll_size":len(ntdll_raw),
        "ntdll_needed":ntdll["needed"],
        "version_arg":"--version",
        "elf_machine":"AArch64",
        "elf_type":"ET_DYN",
        "sha256":digest(raw),
        "size":len(raw),
        "native_needed":loader["needed"],
        "launch_ready":False,
        "installable_as_runtime":False,
        "prefix_created":False,
        "device_tested":False,
        "anti_cheat_supported":False,
    }
    info.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    # Gradle must preserve the attested native code, not strip/alter its hash.
    gradle=upstream/"app/build.gradle"
    content=gradle.read_text(encoding="utf-8")
    if "charoite_wine_loader.so" in content or "charoite_wine_ntdll.so" in content:
        raise ValueError("Native loader Gradle packaging configured twice")
    gradle.write_text(
        content+"\nandroid {\n    packagingOptions {\n"
        '        doNotStrip "**/libcharoite_wine_loader.so"\n'
        '        doNotStrip "**/libcharoite_wine_ntdll.so"\n'
        "    }\n}\n",encoding="utf-8")
    print("CHAROITE_NEXT_WINE_LOADER_PROBE_STAGED=PASS")
    print("WINE_LOADER_SHA256="+digest(raw))
    print("WINE_NTDLL_SHA256="+digest(ntdll_raw))
    print("WINE_LOADER_NEEDED="+",".join(loader["needed"]))
    print("MODERN_LAUNCH_READY=false")
    return evidence

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: stage_native_wine_loader.py VERIFIED_BUNDLE_TAR_GZ NEXT_UPSTREAM_DIR")
    stage(*sys.argv[1:])
