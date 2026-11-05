#!/usr/bin/env python3
"""Package the CI-verified, immutable 111-file Wine29 data cohort as Next assets.

Data-only, never executes Wine/PE. Refuses overwrites and mixed generations.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
BASE_SHA = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
ARCHIVE_SHA = "ada8bd980722deba16e89231652a25a27a7e197a7638abc9d38a61e0614e412e"
SOURCE_RUN = 41947164001
SOURCE_ARTIFACT = 13378882549
VERSION = "wine10-arm64ec-dependencies.0.12-sealed-data-candidate"
ROOT = "charoite-next/wine29-sealed012"
INDEX = ROOT + "/wine29-sealed012-index.json"
MODULES = ROOT + "/modules"
MAX_ITEM = 32 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_ARCHIVE = 128 * 1024 * 1024
NATIVE_KEYS = {"wine", "wineserver", "ntdll_unix"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_archive(path):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ARCHIVE:
        raise ValueError("Missing/linked/oversized pinned sealed Wine29 archive")
    if sha(path.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("Wine29 111-file TAR.GZ hash mismatches successful CI")
    payload = {}
    with tarfile.open(path, "r:gz") as tar:
        members = tar.getmembers()
        allnames = [m.name for m in members]
        if len(allnames) != 112 or len(set(allnames)) != 112 or "manifest.json" not in allnames:
            raise ValueError("Unsealed 111 data files + manifest layout")
        for member in members:
            if (not member.isfile() or member.issym() or member.name.startswith("/") or
                ".." in member.name.split("/") or
                not 0 < member.size <= MAX_ITEM or
                member.mode != 0o444 or member.mtime != 0):
                raise ValueError("Unexpected or unsafe Wine29 archived member")
        manifest = json.load(tar.extractfile("manifest.json"))
        if (manifest.get("schema_version") != 1 or manifest.get("generation") != VERSION or
            manifest.get("android_package") != "com.charoitx" or
            manifest.get("source_commit") != SOURCE or
            manifest.get("baseline_source_archive_sha256") != BASE_SHA or
            manifest.get("file_count") != 111 or manifest.get("pe_dll_count") != 34 or
            manifest.get("wineboot_pe_count") != 1 or manifest.get("nls_count") != 76 or
            manifest.get("native_elf_files_in_bundle") != 0 or
            set(manifest.get("native_elf_source_provenance_only", {})) != NATIVE_KEYS or
            manifest.get("regular_unbundled_import_names") != [] or
            len(manifest.get("delayed_import_owners_outside_cohort", {})) != 15 or
            any(manifest.get(k) is not False for k in
                ("launch_ready", "wineboot_executed", "windows_exe_executed",
                 "wineserver_executed", "prefix_created", "phone_installed"))):
            raise ValueError("Incorrect source provenance or runtime safety labels")
        if manifest.get("immutable_source_run_ids") != {
            "baseline": 41749167248, "six": 41938936238,
            "two": 41940958989, "direct": 41943773293, "mpr": 41943773293
        }:
            raise ValueError("Changed immutable CI source generation")
        expected = manifest.get("files")
        if not isinstance(expected, dict) or set(expected) != (set(allnames) - {"manifest.json"}):
            raise ValueError("Unexpected/missing manifest file paths")
        if len(expected) != 111:
            raise ValueError("Expected 111 source-locked entries")
        for name, rec in expected.items():
            if not (re.fullmatch(r"data/pe/arm64ec/[a-z0-9_]+\.dll", name) or
                    name == "data/pe/arm64/wineboot.exe" or
                    re.fullmatch(r"data/nls/[a-z0-9_]+\.nls", name)):
                raise ValueError("Unexpected bundle path: " + name)
            raw = tar.extractfile(name).read()
            if (not 0 < len(raw) <= MAX_ITEM or rec.get("size") != len(raw) or
                    rec.get("sha256") != sha(raw) or
                    rec.get("cohort") not in {"baseline", "six", "two", "direct", "mpr"}):
                raise ValueError("Wine29 member SHA/size/cohort mismatch: " + name)
            payload[name] = raw
    return manifest, payload


def prepare(archive_arg, checkout_arg):
    archive = Path(archive_arg)
    checkout = Path(checkout_arg)
    if (archive.is_symlink() or checkout.is_symlink() or
        any(x in str(checkout) for x in ("/data/data/", "/data/user/", "/storage/emulated/"))):
        raise ValueError("No device/private storage access")
    archive, checkout = archive.resolve(), checkout.resolve()
    app = checkout / "app/src/main"
    root = app / "assets"
    old = root / "charoite-next/wine29-native07/wine29-native07-index.json"
    old_data = root / "charoite-next/wine29-native07/modules"
    dest = root / ROOT
    if (not (app / "AndroidManifest.xml").is_file() or
            not old.is_file() or not old_data.is_dir() or
            dest.exists() or dest.is_symlink()):
        raise ValueError("Prepared Next .0.7 baseline missing or new data target exists")
    old_index = json.loads(old.read_text(encoding="utf-8"))
    if (old_index.get("archive_sha256") != BASE_SHA or
        old_index.get("module_count") != 100 or
        old_index.get("source_run") != 41749167248):
        raise ValueError("Existing sealed .0.7 source generation changed")
    manifest, payload = validate_archive(archive)
    files, total = [], 0
    for source, raw in sorted(payload.items()):
        path = source[len("data/"):]
        destname = MODULES + "/" + path.replace("/", "_") + ".bin"
        total += len(raw)
        files.append({
            "path": path, "source": source, "asset": destname,
            "size": len(raw), "sha256": sha(raw)
        })
    if (not 0 < total <= MAX_TOTAL or
        len({f["path"] for f in files}) != 111 or
        len({f["asset"] for f in files}) != 111 or
        sum(f["path"].startswith("pe/arm64ec/") for f in files) != 34 or
        sum(f["path"].startswith("nls/") for f in files) != 76 or
        sum(f["path"] == "pe/arm64/wineboot.exe" for f in files) != 1):
        raise ValueError("Sealed 111-file PE/NLS totals inconsistent")
    index = {
        "schema_version": 1, "package": "com.charoitx",
        "bundle_version": VERSION, "wine_source_commit": SOURCE,
        "archive_sha256": ARCHIVE_SHA,
        "source_archive_sha256": BASE_SHA,
        "source_run": SOURCE_RUN, "source_artifact": SOURCE_ARTIFACT,
        "component_count": 35, "pe_count": 35, "nls_count": 76,
        "module_count": 111, "native_elf_count": 3,
        "native_elf_in_sealed_data": False,
        "native_elf_source_provenance_only": manifest["native_elf_source_provenance_only"],
        "regular_unbundled_import_names": [],
        "delayed_unbundled_name_count": 15,
        "modules_total_bytes": total, "module_files": files,
        "module_assets_verified": True, "module_staged_on_phone": False,
        "wine29_pe_nls_runnable": False, "native_elf_executed": False,
        "wineboot_executed": False, "windows_exe_executed": False,
        "wineserver_executed": False, "launch_ready": False,
        "installable_as_runtime": False, "prefix_created": False,
        "device_tested": False, "anti_cheat_supported": False,
    }
    # Source and entire archive verified BEFORE writing generated Next-only assets.
    (dest / "modules").mkdir(parents=True, exist_ok=False)
    for record in files:
        target = root / record["asset"]
        if target.exists() or target.is_symlink():
            raise ValueError("Refuse overwrite of Wine29 data asset")
        target.write_bytes(payload[record["source"]])
    (root / INDEX).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
    if not old.is_file() or not old_data.is_dir():
        raise ValueError("Original Wine29 staged source unexpectedly modified")
    print("WINE29_012_111_PE_NLS_SEPARATE_APK_ASSETS_SHA256=PASS")
    print("WINE29_012_OLD_100_FILE_STAGE_NOT_REPLACED=PASS")
    print("WINE29_012_WINE_WINEBOOT_WINDOWS_EXECUTION=NOT_ATTEMPTED")
    return index


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_wine29_sealed012.py PINNED_111_FILE_TARGZ PREPARED_NEXT_CHECKOUT")
    prepare(sys.argv[1], sys.argv[2])
