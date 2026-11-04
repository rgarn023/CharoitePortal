#!/usr/bin/env python3
"""Stage verified Wine29 .0.7 as a DISTINCT inert Charoite Next APK cohort.

No phone execution, no Wineboot, no prefix, no repack of the older .0.6
Wine29 data cohort. This runs only in the disposable GitHub Actions checkout.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tarfile

SOURCE_RUN = 41749167248
SOURCE_ARTIFACT = 13284932342
SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
VERSION = "wine10-arm64ec-bootstrap.0.7"
PACKAGE = "com.charoitx"
ASSET_ROOT = "charoite-next/wine29-native07"
BUNDLE = ASSET_ROOT + "/wine29-source-matched.bundle"
INDEX = ASSET_ROOT + "/wine29-native07-index.json"
OLD_BUNDLE = "charoite-next/wine-bootstrap-29.bundle"
OLD_INDEX = "charoite-next/wine-bootstrap-29-index.json"
MAX_ARCHIVE = 128 * 1024 * 1024
LIBRARIES = {
    "wine": ("runtime/bin/wine", "libcharoite_wine29_loader.so"),
    "wineserver": ("runtime/bin/wineserver", "libcharoite_wine29_wineserver.so"),
    "ntdll_unix": ("runtime/lib/ntdll.so", "libcharoite_wine29_ntdll.so"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verifier(name, filename):
    location = Path(__file__).resolve().parent / "charoite-wine" / filename
    spec = importlib.util.spec_from_file_location(name, location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def index_for(manifest, report, raw: bytes, older: dict, natives: dict) -> dict:
    if (manifest.get("version") != VERSION or
        manifest.get("source_commit") != SOURCE_SHA or
        manifest.get("android_package") != PACKAGE or
        manifest.get("component_count") != 27 or
        manifest.get("nls_count") != 76 or
        not 0 < len(raw) <= MAX_ARCHIVE or
        older.get("bundle_version") != "wine10-arm64ec-bootstrap.0.6" or
        older.get("source_run") != 41586391767 or
        older.get("source_artifact") != 13208541305 or
        older.get("module_count") != 100 or
        older.get("native_elf_installed") is not False):
        raise ValueError("Missing complete or independent Wine29 generation")
    for flag in ("launch_ready", "installable", "prefix_created",
                 "device_tested", "anti_cheat_supported"):
        if manifest.get(flag) is not False:
            raise ValueError("Wine29 .0.7 incorrectly claims runtime readiness")
    for flag in ("source_native_cohort_verified",):
        if natives.get(flag) is not True:
            raise ValueError("Wine29 native source isolation not verified")
    if (natives.get("source_generation") != VERSION or
        natives.get("native_elf_count") != 3 or
        natives.get("source_component_count") != 27 or
        natives.get("apk_native_install_permitted") is not False or
        natives.get("wineboot_execution_permitted") is not False or
        natives.get("phone_runtime_verified") is not False):
        raise ValueError("Wine29 native gate was not source-only")
    if manifest.get("wine29_native_source_delta_sha256") is None:
        raise ValueError("Wine29 dedicated source proof missing")
    components = manifest["components"]
    nls = manifest["nls_files"]
    if (len(components) != 27 or len(nls) != 76 or
        {name for name, rec in components.items() if rec.get("format") == "ELF"} != set(LIBRARIES)):
        raise ValueError("Wrong native/PE/NLS cohort inventory")
    files = {}
    for key, (source, filename) in LIBRARIES.items():
        rec = components[key]
        if (rec.get("path") != source or rec.get("machine") != "AArch64" or
            rec.get("format") != "ELF" or
            not isinstance(rec.get("load_alignments"), list) or
            not rec["load_alignments"] or
            any(type(n) is not int or n < 16384 for n in rec["load_alignments"]) or
            not isinstance(rec.get("needed"), list) or "libwine.so" in rec["needed"] or
            not isinstance(rec.get("size"), int) or not 0 < rec["size"] <= 32 * 1024 * 1024 or
            not isinstance(rec.get("sha256"), str) or len(rec["sha256"]) != 64):
            raise ValueError("Unsafe source-built Wine29 native ELF: " + key)
        files[key] = {
            "source": source, "filename": filename,
            "sha256": rec["sha256"], "size": rec["size"],
            "machine": "AArch64", "load_alignments": rec["load_alignments"],
            "needed": rec["needed"],
        }
    pe = {name: rec for name, rec in components.items() if rec["format"] == "PE"}
    if len(pe) != 24 or "apisetschema" not in pe or (
        pe["apisetschema"].get("api_set_namespace_version") != 6):
        raise ValueError("Missing source-built API-set namespace v6")
    if not isinstance(report.get("windows_imports_not_bundled"), list):
        raise ValueError("Missing measured PE dependency review")
    return {
        "schema_version": 1, "package": PACKAGE, "source_run": SOURCE_RUN,
        "source_artifact": SOURCE_ARTIFACT, "wine_source_commit": SOURCE_SHA,
        "bundle_version": VERSION, "archive_asset": BUNDLE,
        "archive_size": len(raw), "archive_sha256": sha(raw),
        "original_wine29_asset": OLD_BUNDLE,
        "original_wine29_sha256": older["archive_sha256"],
        "source_delta_sha256": manifest["wine29_native_source_delta_sha256"],
        "source_proof_sha256": manifest["wine29_native_source_proof_sha256"],
        "component_count": 27, "pe_count": 24, "nls_count": 76,
        "native_elf_count": 3,
        "native_components": files,
        "pe_import_gaps": report["windows_imports_not_bundled"],
        "native_elf_in_archive": 3,
        "native_elf_installed_as_apk_libs": True,
        "native_elf_executed": False,
        "windows_exe_executed": False,
        "wineboot_executed": False,
        "source_native_cohort_verified": True,
        "launch_ready": False, "device_tested": False,
        "installable_as_runtime": False, "prefix_created": False,
        "fex_installed": False, "graphics_verified": False,
        "anti_cheat_supported": False,
    }


def stage(archive, upstream):
    archive = Path(archive)
    upstream = Path(upstream)
    if archive.is_symlink() or upstream.is_symlink():
        raise ValueError("Symlink source paths forbidden")
    archive = archive.resolve()
    root = upstream.resolve()
    app = root/"app/src/main"
    if (not app.is_dir() or not (app/"AndroidManifest.xml").is_file() or
        any(x in str(root) for x in ("/data/data/", "/data/user/", "/storage/emulated/")) or
        not archive.is_file() or not 0 < archive.stat().st_size <= MAX_ARCHIVE):
        raise ValueError("Not a new isolated Charoite Next CI source workspace")
    base = app/"assets"
    prev_bundle = base/OLD_BUNDLE
    prev_index = base/OLD_INDEX
    if not (prev_bundle.is_file() and prev_index.is_file()):
        raise ValueError("Frozen Wine29 .0.6 baseline missing")
    prior = json.loads(prev_index.read_text())
    prior_hash = sha(prev_bundle.read_bytes())
    if (prior_hash != prior.get("archive_sha256") or
        prior.get("archive_size") != prev_bundle.stat().st_size):
        raise ValueError("Frozen Wine29 .0.6 archive changed")
    ver = verifier("wine29_new_full_verifier", "verify-bootstrap-bundle.py")
    gate = verifier("wine29_new_native_gate", "verify-wine29-native-isolation.py")
    manifest, review = ver.verify(archive)
    native_result = gate.verify_archive(archive)
    raw = archive.read_bytes()
    index = index_for(manifest, review, raw, prior, native_result)
    stage_dir = base/ASSET_ROOT
    dest_index = base/INDEX
    dest_bundle = base/BUNDLE
    libdir = app/"jniLibs/arm64-v8a"
    gradle = root/"app/build.gradle"
    if (stage_dir.exists() or stage_dir.is_symlink() or dest_index.exists() or
        dest_bundle.exists() or not libdir.is_dir() or not gradle.is_file()):
        raise ValueError("Refusing an existing or unsafe Wine29 .0.7 slot")
    libdest = {k: libdir/v["filename"] for k, v in index["native_components"].items()}
    if any(p.exists() or p.is_symlink() for p in libdest.values()):
        raise ValueError("Refusing existing native Wine29 APK library")
    gradle_text = gradle.read_text(encoding="utf-8")
    if any(p.name in gradle_text for p in libdest.values()):
        raise ValueError("Duplicate Wine29 native doNotStrip rule")
    # Validate every ELF and its source-referenced hash BEFORE ANY file write.
    native_bytes = {}
    with tarfile.open(archive, "r:gz") as tar:
        for key, item in index["native_components"].items():
            member = tar.getmember(item["source"])
            if not member.isfile() or member.size != item["size"]:
                raise ValueError("Changed Wine29 ELF archive member: " + key)
            data = tar.extractfile(member).read()
            if (sha(data) != item["sha256"] or
                data[:6] != b"\x7fELF\x02\x01" or
                struct.unpack_from("<H", data, 18)[0] != 183):
                raise ValueError("Wine29 ABI or native SHA mismatch: " + key)
            native_bytes[key] = data
    if sha(prev_bundle.read_bytes()) != prior_hash:
        raise ValueError("Old Wine29 source archive changed before new staging")
    # The old 0.6 assets and all Wine28/22 native filenames remain untouched.
    stage_dir.mkdir(parents=True, exist_ok=False)
    dest_bundle.write_bytes(raw)
    for key, data in native_bytes.items():
        p = libdest[key]
        p.write_bytes(data)
        p.chmod(0o755)
    dest_index.write_text(json.dumps(index, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    gradle_text += "\nandroid {\n    packagingOptions {\n"
    for key in ("wine", "wineserver", "ntdll_unix"):
        gradle_text += '        doNotStrip "**/' + libdest[key].name + '"\n'
    gradle_text += "    }\n}\n"
    gradle.write_text(gradle_text, encoding="utf-8")
    if sha(prev_bundle.read_bytes()) != prior_hash:
        raise ValueError("Unexpected mutation of frozen Wine29 .0.6 data")
    print("CHAROITE_NEXT_WINE29_07_ARCHIVE_SHA256=PASS")
    print("CHAROITE_NEXT_WINE29_07_NATIVE_ELF_3_HASHES=PASS")
    print("CHAROITE_NEXT_WINE29_06_ORIGINAL_UNCHANGED=PASS")
    print("CHAROITE_NEXT_WINE29_07_PHONE_EXECUTION=NOT_ATTEMPTED")
    print("CHAROITE_NEXT_WINE29_07_LAUNCH_READY=false")
    return index


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_wine29_native07.py VERIFIED_07_ARCHIVE NEW_NEXT_BUILD_TREE")
    stage(sys.argv[1], sys.argv[2])
