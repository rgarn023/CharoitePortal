#!/usr/bin/env python3
"""Read-only Wine29 .0.7 APK-native ELF selector audit for GitHub Actions.

Only inspect immutable, source-indexed CI build files. Never launch Wine,
touch phone storage, create a prefix, or interpret string presence as proof
of a functioning PE loader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED_SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
EXPECTED_RUN = 41749167248
EXPECTED = {
    "wine": ("runtime/bin/wine", "libcharoite_wine29_loader.so"),
    "wineserver": ("runtime/bin/wineserver", "libcharoite_wine29_wineserver.so"),
    "ntdll_unix": ("runtime/lib/ntdll.so", "libcharoite_wine29_ntdll.so"),
}
SELECTORS = (
    "CHAROITE_WINE29_NATIVE_DIR",
    "CHAROITE_WINE29_PE_DIR",
    "CHAROITE_WINE29_DATA_DIR",
    "CHAROITE_WINE28_NATIVE_DIR",
    "CHAROITE_WINE28_PE_DIR",
    "CHAROITE_WINE28_DATA_DIR",
    "WINEDLLPATH",
)
V1_ENV = (
    "CHAROITE_WINE29_NATIVE_DIR",
    "CHAROITE_WINE29_PE_DIR",
    "CHAROITE_WINE29_DATA_DIR",
    "WINEDLLPATH",
)
MAX_ELF_BYTES = 32 * 1024 * 1024


def inspect(index_path: Path, native_dir: Path) -> dict:
    if index_path.is_symlink() or native_dir.is_symlink():
        raise ValueError("Refusing symlink inputs")
    if not index_path.is_file() or not native_dir.is_dir():
        raise ValueError("Wine29 source-indexed build inputs missing")
    if index_path.stat().st_size > 65536:
        raise ValueError("Wine29 source index exceeds bounded size")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if (index.get("package") != "com.charoitx"
            or index.get("schema_version") != 1
            or index.get("source_run") != EXPECTED_RUN
            or index.get("wine_source_commit") != EXPECTED_SOURCE
            or index.get("bundle_version") != "wine10-arm64ec-bootstrap.0.7"
            or index.get("native_elf_count") != 3
            or set(index.get("native_components", {})) != set(EXPECTED)):
        raise ValueError("Wine29 .0.7 source provenance/index mismatch")

    records = {}
    for key, (source, filename) in EXPECTED.items():
        entry = index["native_components"][key]
        target = native_dir / filename
        if (entry.get("source") != source or entry.get("filename") != filename
                or entry.get("machine") != "AArch64" or target.is_symlink()
                or not target.is_file()):
            raise ValueError("Unexpected or missing Wine29 ELF: " + key)
        size = target.stat().st_size
        if not 0 < size <= MAX_ELF_BYTES or entry.get("size") != size:
            raise ValueError("Native ELF size mismatch: " + key)
        data = target.read_bytes()
        if (data[:6] != b"\x7fELF\x02\x01"
                or len(data) < 20
                or struct.unpack_from("<H", data, 18)[0] != 183
                or hashlib.sha256(data).hexdigest() != entry.get("sha256")):
            raise ValueError("Native ELF SHA-256 or AArch64 mismatch: " + key)
        # A literal marker scan, not a disassembler, linker, or runtime test.
        records[key] = {
            "filename": filename,
            "sha256": entry["sha256"],
            "source_sha256_verified": True,
            "literal_markers": {
                name: name.encode("ascii") in data for name in SELECTORS
            },
            "wine29_wine28_conflict_text_present":
                b"Wine29/Wine28 selector conflict" in data,
        }

    coverage = {
        name: [key for key in EXPECTED
               if records[key]["literal_markers"].get(name, False)]
        for name in V1_ENV
    }
    result = {
        "schema_version": 1,
        "scope": "source-matched Wine29 0.7 CI APK native ELF files only",
        "source_run": EXPECTED_RUN,
        "wine_source_commit": EXPECTED_SOURCE,
        "android_package": "com.charoitx",
        "read_only": True,
        "native_elf_hashes_verified": 3,
        "preserved_v1_environment_selector_coverage": coverage,
        "native_elf": records,
        "diagnosis": "INCONCLUSIVE: literal strings alone cannot prove lookup or kernel32 failure",
        "wine_execution": "NOT ATTEMPTED",
        "phone_scratch_or_prefix_access": "NONE",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_index", type=Path)
    parser.add_argument("apk_native_directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.source_index, args.apk_native_directory)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print("WINE29_07_NATIVE_ELF_SELECTOR_AUDIT=PASS_READ_ONLY_INCONCLUSIVE")


if __name__ == "__main__":
    main()
