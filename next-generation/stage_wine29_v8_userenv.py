#!/usr/bin/env python3
"""Pin and stage source-built ARM64X userenv.dll as NEW Next v8 APK data only.

No Wine/process execution, no existing phone prefixes and no prior APK asset writes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

SOURCE_REV = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
SOURCE_RUN = 42419386776
SOURCE_COMMIT = "523e66511a3504f0705eee508c0fc935999dca2f"
SOURCE_ARTIFACT = 13593275372
SOURCE_DIGEST = "sha256:524ed4e41b418095c8cb546e31f0754522ce6c3b8501c643feea826c661fc887"
ROOT = "charoite-next/wine29-v8-userenv"
INDEX = ROOT + "/userenv-index.json"
ASSET = ROOT + "/userenv-arm64.dll.bin"
SOURCE_FILES = {
    "userenv-arm64.dll", "userenv-manifest.json",
    "userenv-pe-header.txt", "userenv-coff-imports.txt",
}
FORBIDDEN = ("/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verified_file(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not (0 < path.stat().st_size <= limit):
        raise ValueError("Untrusted missing/linked/oversized userenv input")
    data = path.read_bytes()
    if len(data) != path.stat().st_size:
        raise ValueError("Unstable source candidate input")
    return data

def verify(artifact: Path):
    if (not artifact.is_absolute() or artifact.is_symlink() or
            not artifact.is_dir() or any(t in str(artifact) for t in FORBIDDEN) or
            {x.name for x in artifact.iterdir()} != SOURCE_FILES):
        raise ValueError("Expected exact immutable source-only v8 candidate folder")
    if any(f.is_symlink() or not f.is_file() for f in artifact.iterdir()):
        raise ValueError("Linked/nonregular source candidate rejected")
    metadata = json.loads(verified_file(artifact / "userenv-manifest.json", 16*1024))
    if (metadata.get("schema_version") != 1
            or metadata.get("generation") != "wine29-v8-userenv-source-candidate"
            or metadata.get("source_commit") != SOURCE_REV
            or metadata.get("source_build_commit") != SOURCE_COMMIT
            or metadata.get("package") != "com.charoitx"
            or metadata.get("file") != "userenv-arm64.dll"
            or metadata.get("image_name") != "userenv.dll"
            or metadata.get("pe_machine") != "0xAA64"
            or metadata.get("sealed_34_provider_count") != 34
            or metadata.get("ordinary_imports_unbundled_after_candidate") != []
            or metadata.get("all_unbundled_after_candidate") != []
            or metadata.get("delay_imports") != []
            or any(metadata.get(key) is not False for key in (
                "native_elf_included","wine_executed","windows_exe_executed",
                "device_tested","prefix_initialized","launch_ready"))):
        raise ValueError("V8 source and import-closure metadata mismatches pinned successful CI")
    dll = verified_file(artifact / "userenv-arm64.dll", 32*1024*1024)
    if len(dll) != metadata.get("size") or sha(dll) != metadata.get("sha256"):
        raise ValueError("V8 candidate bytes do not match source-verified manifest")
    if len(dll)<128 or dll[:2] != b"MZ":
        raise ValueError("V8 candidate missing DOS header")
    off=struct.unpack_from("<I",dll,0x3c)[0]
    if (off<64 or off>len(dll)-24 or dll[off:off+4]!=b"PE\0\0" or
            struct.unpack_from("<H",dll,off+4)[0]!=0xAA64):
        raise ValueError("V8 userenv executable-view machine is not AA64")
    header=verified_file(artifact / "userenv-pe-header.txt", 64*1024).decode("utf-8")
    imports=verified_file(artifact / "userenv-coff-imports.txt", 64*1024).decode("utf-8")
    if ("Format: COFF-ARM64X" not in header
            or "Machine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)" not in header
            or not isinstance(imports,str)):
        raise ValueError("V8 independent ARM64X container/LLVM import evidence invalid")
    spec=importlib.util.spec_from_file_location(
        "wine29_v8_imports",Path(__file__).resolve().parent/"wine29-imports/classify.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ordinary,delayed=module.pe_imports(dll)
    if (ordinary!=metadata.get("ordinary_imports") or delayed!=metadata.get("delay_imports")
            or not ordinary or not all(x.endswith(".dll") and x in imports for x in ordinary)):
        raise ValueError("V8 actual PE import table disagrees with independent source candidate")
    return dll,metadata

def stage(artifact_arg: str, prepared_arg: str):
    artifact,prepared=Path(artifact_arg),Path(prepared_arg)
    for target in (artifact,prepared):
        if (not target.is_absolute() or target.is_symlink()
                or any(v in str(target) for v in FORBIDDEN)):
            raise ValueError("Only isolated GitHub Actions source/checkout supported")
    dll,manifest=verify(artifact)
    app=prepared/"app/src/main"
    assets=app/"assets"
    old=assets/"charoite-next/wine29-sealed012/wine29-sealed012-index.json"
    native=assets/"charoite-next/wine29-v6/wine29-v6-native-index.json"
    services=assets/"charoite-next/wine29-v7-services/services-index.json"
    if not all(x.is_file() and not x.is_symlink() for x in (
        app/"AndroidManifest.xml",old,native,services)):
        raise ValueError("Source-matched prior Next v7 APK preparation absent")
    sealed=json.loads(old.read_text())
    n=json.loads(native.read_text())
    v7=json.loads(services.read_text())
    if (sealed.get("module_count")!=111 or sealed.get("wine_source_commit")!=SOURCE_REV
            or n.get("native_source_revision")!=SOURCE_REV
            or v7.get("wine_source_commit")!=SOURCE_REV
            or v7.get("image_name")!="services.exe"
            or v7.get("source_run")!=42409561051):
        raise ValueError("Source generations do not match sealed 111/v6-native/v7 services")
    if any(row.get("path")=="pe/arm64ec/userenv.dll" for row in sealed["module_files"]):
        raise ValueError("Duplicate userenv provider in prior sealed cohort")
    dest=assets/ROOT
    if dest.exists() or dest.is_symlink():
        raise ValueError("Refusing to overwrite another v8 APK candidate")
    index={
        "schema_version":1, "package":"com.charoitx",
        "wine_source_commit":SOURCE_REV, "source_run":SOURCE_RUN,
        "source_build_commit":SOURCE_COMMIT,
        "source_artifact_id":SOURCE_ARTIFACT,
        "source_artifact_digest":SOURCE_DIGEST,
        "image_name":"userenv.dll","asset":ASSET,
        "size":len(dll),"sha256":sha(dll),"pe_machine":"0xAA64",
        "arm64x_container_machine":"0xA64E",
        "ordinary_imports":manifest["ordinary_imports"],
        "delay_imports":manifest["delay_imports"],
        "ordinary_imports_unbundled_after_candidate":[],
        "all_unbundled_after_candidate":[],
        "previous_sealed_111_unchanged":True,
        "prior_v6_native_cohort_unchanged":True,
        "prior_v7_services_unchanged":True,
        "apk_stage_only":True,
        "windows_executed":False,"prefix_initialized":False,
        "device_tested":False,"launch_ready":False
    }
    dest.mkdir(parents=True,exist_ok=False)
    (assets/ASSET).write_bytes(dll)
    (assets/INDEX).write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    if sha((assets/ASSET).read_bytes())!=manifest["sha256"]:
        raise ValueError("V8 APK copied DLL hash mismatch")
    print("WINE29_V8_SOURCE_VERIFIED_USERENV_APK_STAGE=PASS")
    print("WINE29_V8_SEALED_111_NATIVE_V6_SERVICES_V7_UNCHANGED=PASS")
    print("WINE29_V8_WINEBOOT_SERVICE_AND_PHONE_EXECUTION=NOT_ATTEMPTED")
    return index

if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: stage_wine29_v8_userenv.py ABS_SOURCE_CANDIDATE_DIR ABS_PREPARED_NEXT_CHECKOUT")
    stage(sys.argv[1],sys.argv[2])
