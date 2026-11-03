#!/usr/bin/env python3
"""Read-only preflight for a FUTURE separate Wine29 native source generation.

The signed v0.59 APK deliberately contains inert Wine29 PE/NLS only. This
validator never stages ELF binaries, executes Wine or touches an Android prefix.
A successful source gate is NOT permission to run Wineboot on the phone.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

PINNED_SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
NEXT_COHORT = "wine10-arm64ec-bootstrap.0.7"
OLD_COHORT = "wine10-arm64ec-bootstrap.0.6"
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
NATIVE_MEMBERS = {
    "wine": "runtime/bin/wine",
    "wineserver": "runtime/bin/wineserver",
    "ntdll_unix": "runtime/lib/ntdll.so",
}
# All three must be rebuilt together; matching 0.6 source-data hashes alone
# do NOT establish the correct native loader/search behavior.
REQUIRED_NATIVE_MARKERS = {
    "wine": (b"CHAROITE_WINE29_NATIVE_DIR", b"libcharoite_wine29_ntdll.so"),
    "wineserver": (b"CHAROITE_WINE29_DATA_DIR",),
    "ntdll_unix": (b"CHAROITE_WINE29_PE_DIR", b"CHAROITE_WINE29_DATA_DIR",
                   b"apisetschema.dll"),
}
REQUIRED_SOURCE_MARKERS = (
    b"CHAROITE_WINE29_NATIVE_DIR",
    b"CHAROITE_WINE29_PE_DIR",
    b"CHAROITE_WINE29_DATA_DIR",
    # A future new-generation patch must explicitly reject both selectors
    # being supplied together; merely finding a new env variable is unsafe.
    b"Wine29/Wine28 selector conflict",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(manifest: dict, payloads: dict[str, bytes],
          source_delta: bytes) -> dict:
    """Verify new-generation identity and executable markers; never install."""
    if (manifest.get("version") != NEXT_COHORT or
            manifest.get("version") == OLD_COHORT or
            manifest.get("source_commit") != PINNED_SOURCE or
            manifest.get("android_package") != "com.charoitx" or
            manifest.get("component_count") != 27 or
            manifest.get("nls_count") != 76):
        raise ValueError("Separate Wine29 native source generation not proven")
    for key in ("launch_ready", "installable", "prefix_created",
                "device_tested", "anti_cheat_supported"):
        if manifest.get(key) is not False:
            raise ValueError("Native source archive falsely claims runtime readiness")
    records = manifest.get("components")
    if not isinstance(records, dict) or len(records) != 27:
        raise ValueError("Wrong 27-component native/PE source cohort")
    actual_native = {name for name, item in records.items()
                     if item.get("format") == "ELF"}
    if actual_native != set(NATIVE_MEMBERS) or set(payloads) != actual_native:
        raise ValueError("Incomplete or mixed native ELF source cohort")
    if not isinstance(source_delta, bytes) or any(
            marker not in source_delta for marker in REQUIRED_SOURCE_MARKERS):
        raise ValueError("Wine29 isolated source patch and conflict guard missing")
    for name, expected_path in NATIVE_MEMBERS.items():
        rec = records[name]
        body = payloads[name]
        if (rec.get("path") != expected_path or
                rec.get("machine") != "AArch64" or
                not isinstance(body, bytes) or not 0 < len(body) <= 32 * 1024 * 1024 or
                rec.get("size") != len(body) or
                rec.get("sha256") != sha256(body) or
                body[:6] != b"\x7fELF\x02\x01" or
                not isinstance(rec.get("load_alignments"), list) or
                not rec["load_alignments"] or
                any(type(a) is not int or a < 16384 for a in rec["load_alignments"]) or
                not isinstance(rec.get("needed"), list) or
                "libwine.so" in rec["needed"]):
            raise ValueError("Wine29 ELF ABI, alignment, or source hash mismatch: " + name)
        if any(marker not in body for marker in REQUIRED_NATIVE_MARKERS[name]):
            raise ValueError("Wine29 native loader selector not compiled: " + name)
    return {
        "source_native_cohort_verified": True,
        "native_elf_count": 3,
        "source_component_count": 27,
        "source_generation": NEXT_COHORT,
        "android_package": "com.charoitx",
        "apk_native_install_permitted": False,
        "wineboot_execution_permitted": False,
        "phone_runtime_verified": False,
    }


def verify_archive(archive: Path) -> dict:
    """Re-use the existing complete hash/PE/NLS/archive verifier first."""
    archive = Path(archive)
    if (archive.is_symlink() or not archive.is_file() or
            not 0 < archive.stat().st_size <= MAX_ARCHIVE_BYTES):
        raise ValueError("Missing or unsafe isolated source archive")
    file = Path(__file__).resolve().parent / "verify-bootstrap-bundle.py"
    spec = importlib.util.spec_from_file_location("wine29_archive_verifier", file)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest, _review = verifier.verify(archive)
    with tarfile.open(archive, "r:gz") as tar:
        payloads = {}
        for name, rel in NATIVE_MEMBERS.items():
            member = tar.getmember(rel)
            if not member.isfile() or member.size > 32 * 1024 * 1024:
                raise ValueError("Unsafe Wine29 native ELF member")
            payloads[name] = tar.extractfile(member).read()
        patch = tar.getmember("source/charoite-source-delta.patch")
        if not patch.isfile() or patch.size > 4 * 1024 * 1024:
            raise ValueError("Unsafe Wine29 source delta")
        delta = tar.extractfile(patch).read()
    return check(manifest, payloads, delta)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-wine29-native-isolation.py FUTURE_NEW_SOURCE_ARCHIVE")
    try:
        result = verify_archive(Path(sys.argv[1]))
    except (ValueError, KeyError, tarfile.TarError) as exc:
        print("WINE29_NATIVE_ACTIVATION=BLOCKED: " + str(exc))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True, indent=2))
    print("WINE29_NATIVE_ACTIVATION=NOT_AUTHORIZED; only source preflight passed")
