#!/usr/bin/env python3
"""Stage pinned Windows ARM64 services.exe only into NEW experimental APK assets.
CI packaging only: never executes Wine, services, or touches phone/prefix data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

SOURCE_REV = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
SOURCE_RUN = 42409561051
SOURCE_SHA = "f32a3563254b2ae6447d6cf2e6639be3e7e6d9d9"
SOURCE_ARTIFACT_ID = 13589325323
SOURCE_DIGEST = "sha256:fba183ee44a632c2e45608dace22ce71108129882e2854fd51bf077c04247a34"
ROOT = "charoite-next/wine29-v7-services"
ASSET = ROOT + "/services-arm64.exe.bin"
INDEX = ROOT + "/services-index.json"
INPUT_FILES = {
    "services-arm64.exe", "services-manifest.json",
    "services-pe-header.txt", "services-coff-imports.txt"
}
ORDINARY = [
    "rpcrt4.dll", "advapi32.dll", "userenv.dll", "setupapi.dll",
    "ucrtbase.dll", "kernel32.dll", "ntdll.dll"
]
MAX_BYTES = 16 * 1024 * 1024

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify(artifact: Path):
    if not artifact.is_absolute() or artifact.is_symlink() or not artifact.is_dir():
        raise ValueError("Require isolated absolute source artifact directory")
    if {x.name for x in artifact.iterdir()} != INPUT_FILES:
        raise ValueError("Unexpected services candidate file set")
    if any(x.is_symlink() or not x.is_file() for x in artifact.iterdir()):
        raise ValueError("Linked or nonregular source candidate rejected")
    manifest = json.loads((artifact / "services-manifest.json").read_text())
    if (manifest.get("schema_version") != 1
            or manifest.get("generation") != "wine29-v7-services-source-candidate"
            or manifest.get("source_commit") != SOURCE_REV
            or manifest.get("source_build_commit") != SOURCE_SHA
            or manifest.get("android_package") != "com.charoitx"
            or manifest.get("source_path") != "programs/services/Makefile.in"
            or manifest.get("image_name") != "services.exe"
            or manifest.get("file") != "services-arm64.exe"
            or manifest.get("pe_machine") != "0xAA64"
            or manifest.get("ordinary_imports") != ORDINARY
            or manifest.get("delay_imports") != []
            or any(manifest.get(k) is not False for k in
                   ("native_elf_included", "wine_executed", "windows_exe_executed",
                    "device_tested", "prefix_initialized", "launch_ready"))):
        raise ValueError("Source-built services.exe immutable provenance mismatch")
    binary = (artifact / "services-arm64.exe").read_bytes()
    if (not 1024 < len(binary) <= MAX_BYTES
            or len(binary) != manifest.get("size")
            or sha(binary) != manifest.get("sha256")
            or binary[:2] != b"MZ"):
        raise ValueError("Services.exe SHA/size/DOS header does not match pinned source")
    offset = struct.unpack_from("<I",binary,0x3c)[0]
    if (not 64 <= offset <= len(binary)-24
            or binary[offset:offset+4] != b"PE\0\0"
            or struct.unpack_from("<H",binary,offset+4)[0] != 0xAA64):
        raise ValueError("Services.exe machine must be native Windows ARM64 AA64")
    header = (artifact / "services-pe-header.txt").read_text()
    imports = (artifact / "services-coff-imports.txt").read_text()
    if "ARM64" not in header or "AA64" not in header or any(x not in imports for x in ORDINARY):
        raise ValueError("Independent LLVM PE header/import evidence missing")
    return binary, manifest

def stage(artifact_arg: str, prepared_arg: str):
    artifact, prepared = Path(artifact_arg), Path(prepared_arg)
    for path in (artifact, prepared):
        if not path.is_absolute() or path.is_symlink() or any(x in str(path)
                for x in ("/data/data/","/data/user/","/storage/emulated/")):
            raise ValueError("Only source CI checkout/temporary paths supported")
    binary, original = verify(artifact)
    app = prepared / "app/src/main"
    index = app / "assets/charoite-next/wine29-sealed012/wine29-sealed012-index.json"
    native = app / "assets/charoite-next/wine29-v6/wine29-v6-native-index.json"
    if not (app / "AndroidManifest.xml").is_file() or not index.is_file() or not native.is_file():
        raise ValueError("Expected sealed Wine29 v6 prepared APK base not found")
    sealed = json.loads(index.read_text())
    matched = json.loads(native.read_text())
    if (sealed.get("module_count") != 111
            or sealed.get("wine_source_commit") != SOURCE_REV
            or matched.get("native_source_revision") != SOURCE_REV
            or matched.get("source_run") != 42387905132):
        raise ValueError("V6 native and sealed PE cohorts must remain source-matched")
    root = app / "assets"
    new = root / ROOT
    if new.exists() or new.is_symlink():
        raise ValueError("Refusing to overwrite v7 services APK asset")
    result = {
        "schema_version": 1, "package": "com.charoitx",
        "wine_source_commit": SOURCE_REV,
        "source_run": SOURCE_RUN, "source_build_commit": SOURCE_SHA,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_digest": SOURCE_DIGEST,
        "image_name": "services.exe",
        "pe_machine": "0xAA64", "asset": ASSET,
        "size": len(binary), "sha256": sha(binary),
        "ordinary_imports": ORDINARY, "delay_imports": [],
        "previous_sealed_111_unchanged": True,
        "prior_v6_native_cohort_unchanged": True,
        "apk_stage_only": True, "windows_executed": False,
        "prefix_initialized": False, "device_tested": False,
        "launch_ready": False
    }
    new.mkdir(parents=True, exist_ok=False)
    (root / ASSET).write_bytes(binary)
    (root / INDEX).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if sha((root / ASSET).read_bytes()) != original["sha256"]:
        raise ValueError("V7 APK stage bytes differ from pinned source")
    print("WINE29_V7_SOURCE_BUILT_ARM64_SERVICES_APK_DATA=PASS")
    print("WINE29_V7_PRESERVE_V6_NATIVE_AND_111_PE_NLS=PASS")
    print("WINE29_V7_PHONE_WINEBOOT_AND_SERVICES=NOT_ATTEMPTED")
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_wine29_v7_services.py ABS_ARTIFACT_DIR ABS_PREPARED_NEXT")
    stage(sys.argv[1],sys.argv[2])
