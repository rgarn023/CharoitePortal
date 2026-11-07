#!/usr/bin/env python3
"""Source-matched, read-only Wine29 .0.7 native loader call-site audit.

Inspects a pinned GitHub Actions source bundle and the exact source delta.
No Wine, PE, wineserver, scratch, prefix or phone process is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ARCHIVE_SHA256 = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
PATCH_SHA256 = "f8122ad18663a0bedb5dde7983f6ebb690963ac1c87016fe3d4a1cdbc3061428"
SOURCE_COMMIT = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
SOURCE_MEMBER = "source/charoite-wine29-native-source-delta.patch"
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_PATCH = 1024 * 1024


def analyze_patch(patch: str) -> dict:
    header = "diff --git a/dlls/ntdll/unix/loader.c b/dlls/ntdll/unix/loader.c\n"
    if patch.count(header) != 1:
        raise ValueError("Missing unique ntdll Unix loader source delta")
    block = patch.split(header, 1)[1].split("\ndiff --git ", 1)[0]
    checks = {
        "arm64_pe_search_suffix": 'case IMAGE_FILE_MACHINE_ARM64: return "/aarch64-windows";' in block,
        "dll_path_uses_winedllpath": 'getenv( "WINEDLLPATH" )' in block,
        "source_cohort_requires_three_selectors":
            'if (!native || !pe || !data ||' in block and
            'getenv( "CHAROITE_WINE28_PE_DIR" )' in block and
            'fatal_error( "Wine29/Wine28 selector conflict or incomplete source cohort' in block,
        "wine29_data_dir_selected": 'charoite_wine29_selected_path( "CHAROITE_WINE29_DATA_DIR" )' in block,
        "initial_ntdll_pe_uses_wine29": 'charoite_wine29_selected_path( "CHAROITE_WINE29_PE_DIR" )' in block and
            'asprintf( &name, "%s/ntdll.dll", resolved )' in block,
        "initial_apiset_pe_uses_wine29": 'asprintf( &name, "%s/apisetschema.dll", resolved )' in block,
    }
    if not all(checks.values()):
        raise ValueError("Native source loader path expectation failed: " +
                         ",".join(k for k, v in checks.items() if not v))
    return checks


def inspect(archive: Path) -> dict:
    if archive.is_symlink() or not archive.is_file() or not 0 < archive.stat().st_size <= MAX_ARCHIVE:
        raise ValueError("Missing or oversized source-matched Wine29 archive")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Changed Wine29 .0.7 archive SHA-256")
    with tarfile.open(archive, "r:gz") as tar:
        manifest_member = tar.getmember("manifest.json")
        patch_member = tar.getmember(SOURCE_MEMBER)
        if (not manifest_member.isfile() or manifest_member.size > 65536 or
                not patch_member.isfile() or patch_member.size > MAX_PATCH):
            raise ValueError("Unsafe Wine29 source evidence members")
        manifest = json.load(tar.extractfile(manifest_member))
        patch = tar.extractfile(patch_member).read()
    if (manifest.get("version") != "wine10-arm64ec-bootstrap.0.7" or
            manifest.get("source_commit") != SOURCE_COMMIT or
            manifest.get("android_package") != "com.charoitx" or
            hashlib.sha256(patch).hexdigest() != PATCH_SHA256):
        raise ValueError("Wine29 native source identity mismatch")
    checks = analyze_patch(patch.decode("utf-8"))
    return {
        "schema_version": 1, "source_commit": SOURCE_COMMIT,
        "archive_sha256": ARCHIVE_SHA256, "native_patch_sha256": PATCH_SHA256,
        "inspection": "source-matched patched loader.c change hunks only",
        "call_site_checks": checks,
        "observed": "explicit Wine29 paths for first NTDLL and API-set modules; WINEDLLPATH for general DLL lookup",
        "limitation": "Source patch checks do not prove runtime path choice, kernel32 loading or Wineboot success",
        "wine_or_phone_execution": "NOT ATTEMPTED",
        "prefix_or_scratch_access": "NONE",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.source_archive)
    data = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(data)
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    print("WINE29_07_NATIVE_CALLSITE_AUDIT=PASS_SOURCE_ONLY_NOT_RUNNABLE")


if __name__ == "__main__":
    main()
