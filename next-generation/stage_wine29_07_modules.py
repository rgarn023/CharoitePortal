#!/usr/bin/env python3
"""Add immutable Wine29 .0.7 PE/NLS Android assets to its OWN source cohort.

Run only in a fresh CI checkout AFTER stage_wine29_native07.py. Never
overwrite .0.6, Wine28 or any on-device file. Never invoke Wine/PE/Wineboot.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys
import tarfile

SOURCE_RUN = 41749167248
SOURCE_ARTIFACT = 13284932342
VERSION = "wine10-arm64ec-bootstrap.0.7"
ARCHIVE_SHA = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
ROOT = "charoite-next/wine29-native07"
INDEX = ROOT + "/wine29-native07-index.json"
ARCHIVE = ROOT + "/wine29-source-matched.bundle"
MODULES = ROOT + "/modules"
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_ITEM = 32 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def module_inventory(manifest):
    """Strict source inventory; never treat an ELF as a writable staged file."""
    if (manifest.get("version") != VERSION or
        manifest.get("source_commit") != "c74acb09d51b447f5d5ac56c87608d3ec565a767" or
        manifest.get("component_count") != 27 or
        manifest.get("nls_count") != 76):
        raise ValueError("Wrong Wine29 .0.7 source cohort")
    components = manifest.get("components")
    nls = manifest.get("nls_files")
    if not isinstance(components, dict) or not isinstance(nls, dict):
        raise ValueError("Missing source component dictionary")
    modules = [rec for rec in components.values() if rec.get("format") == "PE"]
    modules.extend(nls.values())
    if len(modules) != 100 or len(nls) != 76 or len(components) != 27:
        raise ValueError("Not exactly 24 Windows PE + 76 Wine NLS")
    files = []
    total = 0
    for rec in modules:
        source = rec.get("path")
        if not isinstance(source, str) or not source.startswith("runtime/"):
            raise ValueError("Unexpected Windows module source path")
        path = source[len("runtime/"):]
        if not (re.fullmatch(r"pe/arm64ec/[a-z0-9_]+\.dll", path) or
                path == "pe/arm64/wineboot.exe" or
                re.fullmatch(r"nls/[a-z0-9_]+\.nls", path)):
            raise ValueError("Unexpected Wine29 PE/NLS path: " + path)
        size, sha = rec.get("size"), rec.get("sha256")
        if (type(size) is not int or not 0 < size <= MAX_ITEM or
            not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{64}", sha)):
            raise ValueError("Invalid PE/NLS hash/size")
        total += size
        files.append({"path": path, "source": source, "size": size,
                      "sha256": sha,
                      "asset": MODULES + "/" + path.replace("/", "_") + ".bin"})
    files.sort(key=lambda r: r["path"])
    if (total > MAX_TOTAL or
        len({r["path"] for r in files}) != 100 or
        len({r["asset"] for r in files}) != 100 or
        sum(r["path"].startswith("nls/") for r in files) != 76 or
        sum(r["path"].startswith("pe/") for r in files) != 24):
        raise ValueError("Duplicate, oversized or mixed Wine29 PE/NLS sources")
    if {r["path"] for r in files if r["path"].startswith("pe/arm64/")} != {
            "pe/arm64/wineboot.exe"}:
        raise ValueError("Missing ARM64-only wineboot data")
    if "pe/arm64ec/apisetschema.dll" not in {r["path"] for r in files}:
        raise ValueError("Missing source-built API-set PE")
    return files, total


def prepare(archive_arg, checkout_arg):
    archive = Path(archive_arg)
    checkout = Path(checkout_arg)
    if archive.is_symlink() or checkout.is_symlink() or (
        any(x in str(checkout) for x in ("/data/user/", "/data/data/", "/storage/emulated/"))):
        raise ValueError("Invalid CI workspace or forbidden device storage")
    archive, checkout = archive.resolve(), checkout.resolve()
    app = checkout / "app/src/main"
    if not (app / "AndroidManifest.xml").is_file():
        raise ValueError("Not a prepared Charoite Next checkout")
    root = app / "assets"
    prior_index = root / INDEX
    prior_archive = root / ARCHIVE
    asset_folder = root / MODULES
    if (not prior_index.is_file() or not prior_archive.is_file() or
        asset_folder.exists() or asset_folder.is_symlink() or
        not archive.is_file() or
        not 0 < archive.stat().st_size <= MAX_ARCHIVE):
        raise ValueError("Wine29 .0.7 baseline absent or target already present")
    pinned = json.loads(prior_index.read_text(encoding="utf-8"))
    if (pinned.get("source_run") != SOURCE_RUN or
        pinned.get("source_artifact") != SOURCE_ARTIFACT or
        pinned.get("bundle_version") != VERSION or
        pinned.get("archive_sha256") != ARCHIVE_SHA or
        pinned.get("module_files") is not None or
        prior_archive.stat().st_size != pinned.get("archive_size") or
        digest(prior_archive.read_bytes()) != ARCHIVE_SHA or
        digest(archive.read_bytes()) != ARCHIVE_SHA):
        raise ValueError("Source match, no-overwrite, or original archive hash failed")

    verifier_file = Path(__file__).resolve().parent / "charoite-wine/verify-bootstrap-bundle.py"
    spec = importlib.util.spec_from_file_location("wine29_full_modules", verifier_file)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest, _review = verifier.verify(archive)
    files, total = module_inventory(manifest)
    bytes_by_name = {}
    # Verify every Windows file in the exact source archive BEFORE writing any file.
    with tarfile.open(archive, "r:gz") as tar:
        for record in files:
            member = tar.getmember(record["source"])
            if not member.isfile() or member.size != record["size"]:
                raise ValueError("Unverified PE/NLS TAR member: " + record["path"])
            data = tar.extractfile(member).read()
            if len(data) != record["size"] or digest(data) != record["sha256"]:
                raise ValueError("Source PE/NLS hash mismatch: " + record["path"])
            bytes_by_name[record["asset"]] = data
    pinned.update({
        "module_count": 100, "modules_total_bytes": total, "module_files": files,
        "module_assets_verified": True, "module_staged_on_phone": False,
        "wine29_pe_nls_runnable": False,
    })
    # Isolated generated APK assets only; .0.6, Wine28 and old prefixes untouched.
    asset_folder.mkdir(parents=True, exist_ok=False)
    for record in files:
        destination = root / record["asset"]
        destination.write_bytes(bytes_by_name[record["asset"]])
    prior_index.write_text(
        json.dumps(pinned, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    assert digest(prior_archive.read_bytes()) == ARCHIVE_SHA
    print("WINE29_07_24_PE_76_NLS_SEPARATE_APK_ASSETS_SHA256=PASS")
    print("WINE29_07_100_SOURCE_FILES_WRITTEN_IN_CI_ONLY=PASS")
    print("WINE29_07_PHONE_STAGING=NOT_ATTEMPTED")
    print("WINE29_07_WINEBOOT_AND_PE_EXECUTION=NOT_ATTEMPTED")
    return pinned


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_wine29_07_modules.py SOURCE_07_ARCHIVE PREPARED_NEXT_CHECKOUT")
    prepare(sys.argv[1], sys.argv[2])
